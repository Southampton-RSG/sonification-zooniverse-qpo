from typing import Dict, List

import numpy as np
from numpy import floating
from numpy.typing import NDArray

import astropy.units as u
from astropy.units import cds
from astropy.time import TimeDelta
from astropy.modeling import Model
from astropy.units import Quantity
from astropy.timeseries import TimeSeries
from mind_the_gaps.simulator import Simulator


def generate_model_from_dict(
        model: Dict[str, any],
        rate_mean: Quantity,
) -> Model:
    """
    Generates an Astropy model from a dictionary that describes it.

    :param model: A dictionary that describes an Astropy model,
        containing `type` (as a base type), `period` (as a quantity), and
        `coherence` and `variance_fraction`.
        Arguably should be unpacked for this function, or made into a dataclass
    :param rate_mean: The mean x-ray count rate, in 1/time units
    """
    return model['type'](
        omega0=2 * np.pi / model['period'].to(u.s).value,
        Q=model['coherence'],
        S0=model['variance_fraction']**2 * rate_mean.to(u.s**-1).value**2,
    )


def generate_synthetic_lightcurve(
        campaign_length: TimeDelta,
        model: Dict[str, any] | List[Dict[str, any]],
        rate_mean: Quantity,
        observation_count: int|None = None,
        observation_cadence: TimeDelta|None = None
) -> TimeSeries:
    """
    Generates a lightcurve of a given model over a specified time.

    :param model: A dictionary, or list of dictionaries, that describe Astropy models
    :param campaign_length: Length of the observation campaign, in time units
    :param rate_mean: The mean x-ray count rate, in 1/time units
    :param observation_count: Number of observations to generate
    :param observation_cadence: Spacing of observations, in time units
    :return: An astropy table, with quantities, corresponding to the lightcurve
    """
    if not isinstance(model, list):
        model = [model]

    if not observation_count:
        observation_count = int(campaign_length / observation_cadence)

    if observation_cadence is not None:
        observation_cadence = campaign_length / observation_count

    print(f"Generating lightcurve for model(s) {' & '.join(model_component['type'].name for model_component in model)}")

    # We generate Astropy models from the dictionaries provided, to feed to the simulator.
    model_components: List[Model] = [
        generate_model_from_dict(
            model_component, rate_mean,
        ) for model_component in model
    ]

    # Initialise the metadata dictionary with the mean rate.
    meta: Dict[str, any] = { 'rate_mean': rate_mean }

    # We add the component (or components) of the model to the metadata for this lightcurve
    for model_component in model:
        for key in ['variance_fraction', 'coherence', 'period']:
            meta[key] = meta.get(key, []) + [model_component[key]]
        meta['type'] = meta.get('type', []) + [model_component['type'].name]

    # Annoyingly, sum() only works on integers (technically might work but not safe/guaranteed)
    model_total: Model = model_components[0]
    for model_component in model_components[1:]:
        model_total += model_component

    lightcurve: TimeSeries = TimeSeries(
        time_start="2024-01-01T00:00:00",
        time_delta=observation_cadence,
        n_samples=observation_count,
        data={
            'rate': np.ones(observation_count) * rate_mean.unit,
            'error': np.zeros(observation_count) * rate_mean.unit,
        },
        meta=meta,
    )

    simulator: Simulator = Simulator(
        model_total,
        lightcurve['time'].mjd,
        lightcurve['rate'].value,
        mean=rate_mean.value,
        pdf="Gaussian",
        extension_factor=2
    )

    rates_clean: NDArray[floating] = simulator.generate_lightcurve()
    rates_noisy, uncertainties = simulator.add_noise(rates_clean)
    lightcurve['rate'] = rates_noisy * rate_mean.unit,
    lightcurve['error'] = uncertainties * rate_mean.unit,
    return lightcurve

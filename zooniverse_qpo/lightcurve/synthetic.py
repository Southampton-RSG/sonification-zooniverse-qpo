from logging import getLogger
from typing import Dict

import numpy as np
from numpy import floating
from numpy.typing import NDArray

from astropy.time import TimeDelta
from astropy.units import Quantity
from astropy.timeseries import TimeSeries
from mind_the_gaps.simulator import Simulator

from zooniverse_qpo.model_definition import ModelDefinitionBase


logger = getLogger(__name__)


def generate_synthetic_lightcurve(
        campaign_length: TimeDelta,
        model_definition: ModelDefinitionBase,
        rate_mean: Quantity,
        observation_count: int|None = None,
        observation_cadence: TimeDelta|None = None
) -> TimeSeries:
    """
    Generates a lightcurve of a given model over a specified time.

    :param model_definition: A defined model to be coverted to astropy format.
    :param campaign_length: Length of the observation campaign, in time units
    :param rate_mean: The mean x-ray count rate, in 1/time units
    :param observation_count: Number of observations to generate
    :param observation_cadence: Spacing of observations, in time units
    :return: An astropy table, with quantities, corresponding to the lightcurve
    """

    if not observation_count:
        observation_count = int(campaign_length / observation_cadence)

    if observation_cadence is not None:
        observation_cadence = campaign_length / observation_count

    # Initialise the metadata dictionary with the mean rate.
    meta: Dict[str, any] = {
        'rate_mean': rate_mean,
        'model_definition': model_definition,
    }

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
        model_definition.get_model_for_mean_rate(rate_mean),
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

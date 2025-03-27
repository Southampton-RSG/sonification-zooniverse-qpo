from itertools import product
from logging import getLogger
from pathlib import Path
from typing import Dict, Generator, Any

import yaml
from astropy.timeseries import TimeSeries
from plotly.graph_objs import Figure
from strauss.sonification import Sonification

from zooniverse_qpo.metadata import write_subject_metadata_to_yaml
from zooniverse_qpo.plotting import plot_lightcurve
from zooniverse_qpo.sonification import generate_sonification_from_lightcurve, write_sonification_to_mp3
from zooniverse_qpo.synthetic.lightcurve import generate_synthetic_lightcurve

logger = getLogger(__name__)


def generate_parameter_grid(
        parameter_grid: Dict,
) -> Generator[Dict, Dict, None]:
    """

    :param parameter_grid:
    :url: https://stackoverflow.com/questions/65392737/python-how-to-create-a-parameter-grid-with-dynamic-number-of-parameters
    :return:
    """
    for vcomb in product(*parameter_grid.values()):
        yield dict(zip(parameter_grid.keys(), vcomb))


def generate_synthetic_subjects(subject_sets: Dict[str, Any], root_path: Path):
    """
    Creates synthetic Zooniverse subjects for the given subject set parameter definition.

    :param subject_sets:
    :param output_path:
    :return:
    """
    for subject_set_slug, subject_set in subject_sets.items():
        subject_set_path: Path = root_path / subject_set_slug
        logger.debug(
            f"{subject_set_path}: Creating subjects for subject set:\n{subject_set}"
        )
        if not subject_set_path.exists():
            subject_set_path.mkdir(parents=True)
            with (subject_set_path / 'meta.yaml').open('w') as subject_set_meta_file:
                yaml.dump(subject_set['meta'], subject_set_meta_file)

        # TODO: Better name creation than 'enumerate'
        for idx, parameters in enumerate(generate_parameter_grid(subject_set['parameters'])):
            logger.debug(
                f"Generating lightcurves for subject set {idx}:\n{parameters}"
            )

            lightcurve: TimeSeries = generate_synthetic_lightcurve(
                campaign_length=parameters['campaign_length'],
                observation_cadence=parameters.get('observation_cadence', None),
                observation_count=parameters.get('observation_count', None),
                rate_mean=parameters['rate_mean'],
                model_definition=parameters['model_definition'],
            )
            figure: Figure = plot_lightcurve(lightcurve)
            sonification: Sonification = generate_sonification_from_lightcurve(
                lightcurve=lightcurve,
                sampler=parameters['sampler'][1],
                tempo=parameters['tempo'],
            )

            output_path: Path = subject_set_path / f"test-{idx}"
            figure.write_html(output_path.with_suffix(".html"))
            write_sonification_to_mp3(sonification, output_path=output_path)
            write_subject_metadata_to_yaml(
                name=f"{subject_set['meta']['display_name']} - {idx}",
                parameters=parameters,
                output_path=output_path.with_suffix(".meta.yaml"),
            )

from logging import getLogger, Logger
from pathlib import Path
from typing import Dict, Any
from uuid import uuid4

import yaml
from astropy.timeseries import TimeSeries
from plotly.graph_objs import Figure
from stingray import Lightcurve
from strauss.sonification import Sonification

from zooniverse_qpo.lightcurve.observed import load_observational_data
from zooniverse_qpo.lightcurve.synthetic import generate_synthetic_lightcurve
from zooniverse_qpo.metadata import write_subject_metadata_to_yaml
from zooniverse_qpo.parameters import generate_parameter_grid
from zooniverse_qpo.plotting import plot_lightcurve
from zooniverse_qpo.sonification import generate_sonification_from_lightcurve, write_sonification_to_mp3, write_sonification_to_mp4


logger: Logger = getLogger(__name__)


def write_subject_data(
        lightcurve: TimeSeries,
        output_path: Path,
        parameters: Dict[str, Any],
        plot_parameters: Dict[str, Any],
        name: str,
):
    """

    :param lightcurve:
    :param output_path:
    :param parameters:
    :param name:
    :param plot_title:
    :return:
    """
    figure: Figure = plot_lightcurve(
        lightcurve,
        title=plot_parameters['title'],
        period=plot_parameters.get('period', None),
    )
    sonification: Sonification = generate_sonification_from_lightcurve(
        lightcurve=lightcurve,
        sampler=parameters['sampler'][1],
        tempo=parameters['tempo'],
    )

    figure.write_html(output_path.with_suffix(".html"))
    # write_sonification_to_mp3(sonification, output_path=output_path)
    write_sonification_to_mp4(sonification, output_path=output_path)
    write_subject_metadata_to_yaml(
        name=name,
        parameters=parameters,
        output_path=output_path.with_suffix(".meta.yaml"),
    )


def generate_observed_subject_data(
        subject_sets: Dict[str, Any],
        root_path: Path
):
    """
    Creates Zooniverse subjects from the observational data for a set of parameter definitions.

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

        for parameters in generate_parameter_grid(subject_set['parameters']):
            logger.debug(
                f"Generating lightcurves for observed file:\n{parameters}"
            )

            lightcurve: TimeSeries = load_observational_data(
                parameters['file'],
                format=parameters['format']['type'],
                units=parameters['format']['units'],
                column_mapping=parameters['format']['mapping'],
                length=parameters['length'],
            )
            write_subject_data(
                lightcurve=lightcurve,
                parameters=parameters,
                output_path=subject_set_path / parameters['file'].stem,
                name=f'{parameters['file'].relative_to(parameters['file'].parent)}',
                plot_parameters={
                    'title': f'{parameters['file'].relative_to(parameters['file'].parent)}',
                }
            )


def generate_synthetic_subject_data(
        subject_sets: Dict[str, Any],
        root_path: Path
):
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
            write_subject_data(
                lightcurve=lightcurve,
                parameters=parameters,
                output_path=subject_set_path / f'subject_{uuid4()}',
                name=f'{subject_set_slug}_{idx}',
                plot_parameters={
                    'title': lightcurve.meta['model_definition'].get_title(),
                    'period': 'auto',
                }
            )

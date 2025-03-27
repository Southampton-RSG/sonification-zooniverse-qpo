import yaml
from pathlib import Path
from typing import Dict, Any
from logging import getLogger, Logger

from astropy import units as u
from astropy.time import TimeDelta
from astropy.timeseries import TimeSeries
from astropy.units import Quantity


logger: Logger = getLogger(__name__)


def write_subject_metadata_to_yaml(
        name: str,
        parameters: Dict,
        output_path: Path,
):
    """
    Converts the parameters used to create a subject into a metadata file to be sent up to the Zooniverse.

    :param name: The name of the subject.
    :param parameters: The parameters used to generate the subject.
    :param output_path: The path to write the file to.
    :return:
    """
    with output_path.with_suffix('.yaml').open('w') as output_file:
        # We wrap everything in string conversion as Astropy converts things into numerical-but-still-fancy types
        # And yaml dumps them out as a mess.
        metadata: Dict[str, Any] = parameters.copy()

        campaign_length: TimeDelta|None = metadata.pop("campaign_length", None)
        observation_cadence: TimeDelta|None = metadata.pop("observation_cadence", None)
        observation_count: int|None = metadata.pop("observation_count", None)

        metadata['name'] = name
        metadata['instrument'] = metadata.pop('sampler')[0]
        metadata['rate_mean'] = f"{metadata.pop('rate_mean')}"
        metadata['campaign_length'] = f"{campaign_length.to(u.day)}" if campaign_length else None
        metadata['observation_count'] = observation_count
        metadata['observation_cadence'] = f"{observation_cadence.to(u.day)}" if observation_cadence else None
        metadata.update(metadata.pop('model_definition').to_metadata())

        logger.debug(
            f"Writing metadata to YAML file:\n{metadata}"
        )
        yaml.dump(metadata, output_file)

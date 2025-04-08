import yaml
from logging import getLogger, Logger
from pathlib import Path
from typing import Dict, Any, List

from astropy import units as u
from astropy.time import TimeBase
from astropy.units import Quantity, UnitBase


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
        metadata: Dict[str, Any] = {}

        for key, value in parameters.items():
            if isinstance(value, TimeBase):
                metadata[key] = f"{parameters[key].to(u.day)}"

            elif isinstance(value, dict):
                # We ignore things like units and column mapping
                pass

            elif isinstance(value, Quantity) or isinstance(value, UnitBase) or isinstance(value, Path):
                logger.debug(f"Converting {key}: {value}")
                metadata[key] = f"{parameters[key]}"

            elif key == 'sampler':
                metadata[key] = parameters[key][0]
            elif key == 'model_definition':
                metadata.update(
                    parameters[key].to_metadata()
                )
            else:
                metadata[key] = value

        logger.debug(
            f"Writing metadata to YAML file:\n{metadata}"
        )
        yaml.dump(metadata, output_file)

import yaml
from pathlib import Path
from typing import Dict
from logging import getLogger

from astropy.timeseries import TimeSeries
from astropy import units as u


logger = getLogger(__name__)


def write_subject_metadata_to_yaml(
        lightcurve: TimeSeries,
        sonification_meta: Dict,
        output_path: Path
):
    """

    :param lightcurve:
    :param sonification_meta:
    :param output_path:
    :return:
    """
    with output_path.with_suffix('.yaml').open('w') as output_file:
        # We wrap everything in string conversion as Astropy converts things into numerical-but-still-fancy types
        # And yaml dumps them out as a mess.
        metadata = {} | sonification_meta
        metadata[f"rate_mean"] = f"{lightcurve.meta['rate_mean'].to(u.s**-1)}"

        for idx in range(len(lightcurve.meta['type'])):
            metadata[f"period_{idx}"] = f"{lightcurve.meta['period'][idx].to(u.d)}"
            metadata[f"coherence_{idx}"] = lightcurve.meta['coherence'][idx]
            metadata[f"variance_fraction_{idx}"] = lightcurve.meta['variance_fraction'][idx]
            metadata[f"type_{idx}"] = f"{lightcurve.meta['type'][idx]}"

        logger.debug(
            f"Writing metadata to YAML file:\n{metadata}"
        )

        yaml.dump(metadata, output_file)

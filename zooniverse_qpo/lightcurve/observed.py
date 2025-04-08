from logging import getLogger
from pathlib import Path
from typing import Dict
from random import random, randint

from astropy import units as u
from astropy.time import Time, TimeDelta
from astropy.timeseries import TimeSeries
from astropy.units import UnitBase

logger = getLogger(__name__)


def load_observational_data(
        file_path: Path,
        format: str|None = "ascii",
        time_column: str|None = "time",
        time_format: str|None = 'mjd',
        units: Dict[str, UnitBase]|None =None,
        column_mapping: Dict[str, str]|None =None,
        length: UnitBase|None =None,
) -> TimeSeries:
    """

    :param file_path:
    :param format:
    :param time_column:
    :param time_format:
    :param units:
    :param column_mapping:
    :param length:
    :return:
    """
    if column_mapping is None:
        column_mapping: Dict[str, str] = {
            'rate': 'rate',
            'error': 'error',
        }
    if units is None:
        units: Dict[str, UnitBase] = {
            'rate': 1 / u.s,
            'error': 1 / u.s,
        }

    lightcurve: TimeSeries = TimeSeries.read(
        file_path,
        format=format,
        time_column=time_column,
        time_format=time_format,
        units=units,
    )

    for file_column, standard_column in column_mapping.items():
        lightcurve.rename_column(file_column, standard_column)

    if length is not None:
        index_start: int = randint(0, len(lightcurve))
        time_start: Time = lightcurve.time[index_start]
        lightcurve = lightcurve.loc[time_start:time_start+length]

    return lightcurve

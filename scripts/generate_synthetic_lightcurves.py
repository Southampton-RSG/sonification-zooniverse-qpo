"""

"""
import copy
from logging import Logger, FileHandler, DEBUG, getLogger, Formatter, StreamHandler
from pathlib import Path
from configparser import ConfigParser

import yaml
from astropy import units as u
from astropy.units import Quantity
from astropy.time import TimeDelta
from astropy.timeseries import TimeSeries

from mind_the_gaps.models.psd_models import Lorentzian, BendingPowerlaw

from plotly.graph_objs import Figure

from strauss.generator import Sampler
from strauss.sonification import Sonification

from zooniverse_qpo.metadata import write_subject_metadata_to_yaml
from zooniverse_qpo.sonification import generate_sonification_from_lightcurve, write_sonification_to_mp3
from zooniverse_qpo.synthetic import generate_synthetic_lightcurve
from zooniverse_qpo.plotting import plot_lightcurve


def main():
    config: ConfigParser = ConfigParser()
    config.read(
        [
            'settings.default.ini', 'settings.ini'
        ]
    )

    logger: Logger = getLogger('zooniverse_qpo')
    logger.setLevel(DEBUG)

    file_handler: FileHandler = FileHandler(Path(config['PATHS']['logs']) / 'generate_synthetic_lightcurves.log')
    # stream_handler: StreamHandler = StreamHandler()

    log_formatter: Formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(log_formatter)
    # stream_handler.setFormatter(log_formatter)

    logger.addHandler(file_handler)
    # logger.addHandler(stream_handler)

    standard_campaign_length: Quantity = TimeDelta(360, format='jd')
    standard_period: TimeDelta = TimeDelta(21, format='jd')
    standard_cadence: TimeDelta = TimeDelta(3, format='jd')
    standard_rate_mean: Quantity = 25 * u.s ** -1
    standard_coherence: float = 5

    lightcurve_bpl: TimeSeries = generate_synthetic_lightcurve(
        campaign_length=standard_campaign_length,
        observation_cadence=standard_cadence,
        rate_mean=standard_rate_mean,
        model={
            'type': BendingPowerlaw, 'period': standard_period,
            'coherence': standard_coherence, 'variance_fraction': 0.3
        },
    )
    figure_bpl: Figure = plot_lightcurve(lightcurve_bpl)

    # lightcurve_lorentzian: TimeSeries = generate_synthetic_lightcurve(
    #     campaign_length=standard_campaign_length,
    #     observation_cadence=standard_cadence,
    #     rate_mean=standard_rate_mean,
    #     model={
    #         'type': Lorentzian, 'period': standard_period,
    #         'coherence': standard_coherence, 'variance_fraction': 0.3
    #     },
    # )
    # lightcurve_mixed: TimeSeries = generate_synthetic_lightcurve(
    #     campaign_length=standard_campaign_length,
    #     observation_cadence=standard_cadence,
    #     rate_mean=standard_rate_mean,
    #     model=[
    #         {
    #             'type': BendingPowerlaw, 'period': standard_period,
    #             'coherence': standard_coherence, 'variance_fraction': 0.2
    #         },
    #         {
    #             'type': Lorentzian, 'period': standard_period,
    #             'coherence': standard_coherence, 'variance_fraction': 0.2
    #         },
    #     ],
    # )

    soundfont_path: Path = Path(config['PATHS']['soundfonts'])

    flute_sampler: Sampler = Sampler(soundfont_path / "flute.sf2")
    flute_sampler_staccato: Sampler = copy.copy(flute_sampler)
    flute_sampler_staccato.load_preset('staccato')

    flute_sampler_long: Sampler = copy.copy(flute_sampler)
    flute_sampler_long.modify_preset(
        {
            'note_length': 0.15,  # hold each note for 0.03 seconds or 30 ms - what if this was 1s?
            'volume_envelope': {
                'use': 'on',
                # A,D,R values in seconds, S sustain fraction from 0-1 that note
                # will 'decay' to (after time A+D)
                'A': 0.01,  # ✏️ Time to fade in note to maximum volume, using 10 ms
                'D': 0.0,  # ✏️ Time to fall from maximum volume to sustained level (s), irrelevant while S is 1
                'S': 1.,  # ✏️ fraction of maximum volume to sustain note at while held, 1 implies 100%
                'R': 0.07,  # ✏️ Time to fade out once note is released, using 100 ms
            }
        }
    )

    sonification_bpl: Sonification = generate_sonification_from_lightcurve(
        lightcurve=lightcurve_bpl,
        sampler=flute_sampler_long,
        tempo=config['SONIFICATION'].getint('tempo')
    )
    output_path: Path = Path(config['PATHS']['zooniverse']) / 'test' / 'lightcurve_bpl.mp3'
    write_sonification_to_mp3(sonification_bpl, output_path=output_path)
    figure_bpl.write_html(output_path.with_suffix('.html'))
    write_subject_metadata_to_yaml(
        lightcurve=lightcurve_bpl,
        sonification_meta={'tempo': 6, 'instrument': 'Flute, staccato'},
        output_path=output_path,
    )

if __name__ == "__main__":
    main()

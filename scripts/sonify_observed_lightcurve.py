"""

"""
import copy
from configparser import ConfigParser
from logging import Logger, FileHandler, DEBUG, getLogger, Formatter
from pathlib import Path
from typing import Dict

from astropy import units as u

from strauss.generator import Sampler

from zooniverse_qpo.subject.output import generate_observed_subject_data


def main():
    config: ConfigParser = ConfigParser()
    config.read(
        ['settings.default.ini', 'settings.ini']
    )
    paths: Dict[str, Path] = {
        key: Path(value) for key, value in config['PATHS'].items()
    }

    logger: Logger = getLogger('zooniverse_qpo')
    logger.setLevel(DEBUG)

    file_handler: FileHandler = FileHandler(Path(config['PATHS']['logs']) / 'sonify_observed_lightcurves.log')
    log_formatter: Formatter = Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    soundfont_path: Path = paths['soundfonts']

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

    generate_observed_subject_data(
        root_path=paths['zooniverse'] / 'subjects',
        subject_sets={
            'flute_staccato': {
                'meta': {
                    'display_name': "Flute, Staccato",
                },
                'parameters': {
                    'file': paths['observed'] / 'RE_J1034+396.dat',
                    'format': {
                        'type': 'ascii',
                        'time': {
                            'format': 'mjd',
                            'column': 'time',
                        },
                        'units': {
                            'rate': 1/ u.s,
                            'err': 1 / u.s,
                        },
                        'mapping': {
                            'err': 'error',
                        }
                    },
                    'length': [17.3 * 3550 * u.s] * 5,
                    'sampler': ('Flute, staccato', flute_sampler_staccato),
                    'tempo': 4,
                },
            },
        }
    )

if __name__ == "__main__":
    main()

from pathlib import Path
from typing import List, Tuple, Dict

from numpy import floating
from numpy.typing import NDArray

from astropy.timeseries import TimeSeries

from strauss.score import Score
from strauss.generator import Sampler
from strauss.sources import Objects, Events
from strauss.sonification import Sonification

from moviepy import AudioFileClip, VideoFileClip,ColorClip


# C-Major pentatonic, from Strauss example
NOTE_SCALE: List[List[str]] = [
    ["C3","D3","E3","G3","B3","C4","D4","E4","G4","B4","C5","D5","E5","G5","B5"]
]


def generate_sonification_from_lightcurve(
    lightcurve: TimeSeries,
    sampler: Sampler,
    tempo: int = 6,
):
    """

    :param lightcurve:
    :param sampler:
    :param tempo: Target notes/second
    :return:
    """
    system: str = "mono"
    score: Score =  Score(
        NOTE_SCALE, len(lightcurve) / tempo,
    )
    maps: Dict[str, NDArray[floating]] = {
        'time': lightcurve['time'].mjd,
        'pitch': lightcurve['rate'].value,
    }

    lims: Dict[str, Tuple[str, str]] = {
        'time': ('0','105'),
        'pitch': ('0','100')
    }
    # set 0 to 100 percentile limits so the full pitch range is used...
    # setting 0 to 105 for time means the sonification is 5% longer than
    # the time needed to trigger each note - by making this more than 100%
    # we give all the notes time to ring out (setting this at 100% means
    # the final note is triggered at the moment the sonification ends)

    # set up source
    sources: Events = Events(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=lims)

    soni: Sonification = Sonification(score, sources, sampler, system)
    soni.render()
    return soni


def write_sonification_to_mp3(soni: Sonification, output_path: Path):
    """

    :param soni:
    :param output_directory:
    :return:
    """
    path_wav: Path = output_path.with_suffix('.wav')
    path_mp3: Path = output_path.with_suffix('.mp3')

    soni.save(fname=path_wav)
    AudioFileClip(path_wav).write_audiofile(path_mp3, codec='mp3')
    path_wav.unlink()


def write_sonification_to_mp4(soni: Sonification, output_path: Path):
    """

    :param soni:
    :param output_directory:
    :return:
    """
    path_wav: Path = output_path.with_suffix('.wav')
    path_mp4: Path = output_path.with_suffix('.mp4')

    soni.save(fname=path_wav)
    audio: AudioFileClip = AudioFileClip(path_wav)
    video: ColorClip = ColorClip(
        size=(256,1),
        color=(0,0,0),
        duration=audio.duration
    )
    video.audio = audio
    video.write_videofile(
        filename=path_mp4,
        fps=60
    )

    path_wav.unlink()
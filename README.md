## UV

To run the notebooks using UV:

```
uv run --with jupyter jupyter lab
```

# tess-audio-utils
Python functions for sonification of TESS light curves. Requires Python 3.8. Uses [STRAUSS](https://github.com/james-trayford/strauss) to generate audio from `x,y` data for each light curve, and [`conda`](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) for package management.

1. Install dependencies in their own `conda` environment:
    ```sh
    conda env create -f environment.yml
    conda activate tess-audio-utils
    ```
1. Run `tess_examples.py` or `tess_subjects.py` to generate a set of WAV files with STRAUSS.
1. Once you've got the WAV files, you can convert them to MP3 with the ffmpeg shell scripts.
1. `create_subjects.py` will create new Panoptes subjects from a list of PH-TESS subject IDs and the MP3 files that you've created in previous steps.

## Python scripts

- `create_subjects.py`: Create new Panoptes subjects from a list of PH-TESS subject IDs and a set of MP3 files.
- `tess_examples.py`: Generate a set of WAV files from a list of PH-TESS subject IDs.
- `tess_subjects.py`: Generate a set of WAV files for a given PH-TESS subject set ID.
- `subject_utils.py`: A collection of utility functions for reading light curve data and converting it to sound.
  - `fetch_light_curve`: Return the light curve data, given the URL of a JSON file
    ```python
    from subject_utils import fetch_light_curve
    days, fluxes = fetch_light_curve(url)
    ```
  - `light_curve_url`: Returns the URL of the light curve data for a given subject.
    ```python
    from subject_utils import light_curve_url
    url = light_curve_url(subject)
    ```
  - `normalise_light_curve`: Normalise the light curve data to a [0…1] range in both axes.
    ```python
    from subject_utils import normalise_light_curve
    x, y = normalise_light_curve(days, fluxes)
    ```
  - `sonify`: Create a STRAUSS sonification, which can be rendered and saved. The `x,y` data series must be converted to a set of STRAUSS parameters first.
    ```python
    from subject_utils import sonify
    data = {
      'pitch':1.,
      'time_evo':x,
      'azimuth':(x*0.5+0.25) % 1,
      'polar':0.5,
      'pitch_shift':(y*10+1)**-0.7
    }

    soni = sonify(data)
    soni.render()
    ```

## ffmpeg scripts
- `examples2mp3.sh`: convert the WAV files in `wav/examples` to MP3 files in `mp3/examples`.
- `sims2mp3.sh`: convert the WAV files in `wav/sims` to MP3 files in `mp3/sims`.

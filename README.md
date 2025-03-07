[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14920090.svg)](https://doi.org/10.5281/zenodo.14920090)
![Python](https://img.shields.io/badge/python-3.8-blue)

# TomoSNR

TomoSNR randomly simulates noise in tomographic models and calculates a signal to noise ratio. This is done by taking the spherical wavelet transform of the model, and simulating random versions of the small scale information.

## Installation and Dependencies

For now, this is pinned to python3.8.
The main dependencies are [`healpy`](https://healpy.readthedocs.io/), [`pys2let`](http://astro-informatics.github.io/s2let/) and [`joblib`](https://joblib.readthedocs.io/en/stable/).

To install the package and dependencies, clone the repo and run `pip install .`.
Run `pip install ".[example]"` to also install dependencies to run the notebook in the `example` directory.

## Usage

From the command line, for the serial implementation

`tomosnr <input_files> <options>`

`<input_files>` are 2D maps, saved as `.fits` files using the HEALPix pixelisation scheme.  We provide helper functions in the `tomosnr.utils` module convert from (lat, lon) to HEALPix.

Output files are save in the `outputs` directory.  If no `outputs` directory exists in the directory where the program was called, one is created.  Note that rerunning the program will overwrite previous saved outputs files.

For a full description of command line options run `tomosnr --help`.

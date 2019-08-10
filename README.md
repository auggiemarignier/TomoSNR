# TomoS2N

TomoS2N randomly simmulates noise in tomographic models and calculates a signal to noise ratio. This is done by taking the spherical wavelet transform of the model, and simulating random versions of the small scale information.

## Installation and Dependencies

Clone the repo and direct the command line to where you have the repo saved.  
Type `python setup.py install`

The main dependencies are [`healpy`](https://healpy.readthedocs.io/), [`s2let`](http://astro-informatics.github.io/s2let/), [`massmappy`](https://astro-informatics.github.io/massmappy/), and [`mpi4py`](https://mpi4py.readthedocs.io/).

## Usage

From the command line

`tomos2n <input_files> <options>`

`<input_files>` are 2D maps, saved as `.fits` files using the HEALPix pixelisation scheme.

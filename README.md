[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3594850.svg)](https://doi.org/10.5281/zenodo.3594850)


# TomoSNR

TomoS2N randomly simmulates noise in tomographic models and calculates a signal to noise ratio. This is done by taking the spherical wavelet transform of the model, and simulating random versions of the small scale information.

## Installation and Dependencies

Clone the repo and direct the command line to where you have the repo saved.  
Type `python setup.py install`

The main dependencies are [`healpy`](https://healpy.readthedocs.io/), [`s2let`](http://astro-informatics.github.io/s2let/) and [`mpi4py`](https://mpi4py.readthedocs.io/).

## Usage

From the command line, for the serial implementation

`tomos2n <input_files> <options>`

and for the parallel implementation

`mpirun -np <nproc> tomos2n <input_riles> -P <options>`

`<input_files>` are 2D maps, saved as `.fits` files using the HEALPix pixelisation scheme.

Output files are save in the `outputs` directory.  If no `outputs` directory exists in the directory where the program was called, one is created.  Note that rerunning the program will overwrite previous saved outputs files.

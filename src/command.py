from .random_realisations import run, run_par
from argparse import ArgumentParser
import os


def process():
    parser = ArgumentParser(
        description="Measure the S2N in your tomographic model by generating a bunch of random noise realisations."
    )
    parser.add_argument(
        "infiles",
        nargs="+",
        type=str,
        help="Input filenames.  Must be HealPix maps in .fits files.",
    )
    parser.add_argument(
        "-L", default=35, type=int, help="Maximum angular degree.  Positive integer."
    )
    parser.add_argument(
        "-B", default=1.5, type=float, help="Wavelet parameter. Positive number > 1."
    )
    parser.add_argument(
        "-J",
        default=2,
        type=int,
        help="Minimum wavelet scale in transform. Positive integer.",
    )
    parser.add_argument(
        "-s",
        "--simscales",
        nargs="+",
        default=-1,
        type=int,
        help="List of wavelet scales to be simulated, indexed from 0. Integer.",
    )
    parser.add_argument(
        "-n",
        "--nmaps",
        default=500,
        type=int,
        help="Number of random maps to be generated.  Positive integer.",
    )
    parser.add_argument(
        "-t",
        "--tilesize",
        default=8,
        type=int,
        help="Defines the size of tile as ARGxARG degrees.  Current accepted values are 8,14,42 and 42.",
    )
    parser.add_argument(
        "--textsave",
        action="store_true",
        help="With this flag, outputs are saved as text files rather than binaries.",
    )
    parser.add_argument(
        "-P",
        "--parallel",
        action="store_true",
        help="Implements the parallel implementation.  Call using mpirun -np <nproc>",
    )

    arguments = parser.parse_args()

    infiles = arguments.infiles
    L = arguments.L
    B = arguments.B
    J_min = arguments.J
    simscales = arguments.simscales
    nmaps = arguments.nmaps
    par = arguments.parallel
    binsave = not arguments.textsave
    tilesize = arguments.tilesize

    if not os.path.isdir("./outputs"):
        os.mkdir("./outputs")

    if not par:
        for i, infile in enumerate(infiles, 1):
            print(infile)
            run(
                infile,
                L=L,
                B=B,
                J_min=J_min,
                simscales=simscales,
                nmaps=nmaps,
                tilesize=tilesize,
                binsave=binsave,
                save_append=i,
            )
    if par:
        run_par(
            infiles,
            L=L,
            B=B,
            J_min=J_min,
            simscales=simscales,
            nmaps=nmaps,
            tilesize=tilesize,
            binsave=binsave,
        )


if __name__ == "__main__":
    process()

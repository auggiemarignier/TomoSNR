from .random_realisations import *
from argparse import ArgumentParser
from mpi4py import MPI    
import sys

def process():
    parser = ArgumentParser(description='Measure the S2N in your tomographic model by generating a bunch of random noise realisations.')
    parser.add_argument('infiles',nargs='*',help='Input filenames.  Must be HealPix maps in .fits files.')
    parser.add_argument('-L',default=35,type=int,help='Maximum angular degree.  Positive integer.')
    parser.add_argument('-B',default=1.5,type=float,help='Wavelet parameter. Positive number > 1.')
    parser.add_argument('-J',default=2,type=int,help='Minimum wavelet scale in transform. Positive integer.')
    parser.add_argument('-m','--maxscale',default=6,type=int,help='Maximum wavelet scale for which the original is kept.  All greater scales get simmulated. Positive integer.')
    parser.add_argument('-n','--nmaps',default=500,type=int,help='Number of random maps to be generated.  Positive integer.')
    parser.add_argument('-t','--textsave',action='store_true',help='With this flag, outputs are saved as text files rather than binaries.')
    parser.add_argument('-N','--nproc',default=1,type=int,help='Number of processors for parallel operation.  Each processor works on a single input file. Positive Integer.')

    arguments = parser.parse_args()

    infiles = arguments.infiles
    L = arguments.L
    B = arguments.B
    J_min = arguments.J
    maxscale = arguments.maxscale
    nmaps = arguments.nmaps
    nproc = arguments.nproc
    binsave = not arguments.textsave

    if not os.path.isdir('./outputs'):
        os.mkdir('./outputs')

    if nproc == 1:
        run(infiles,L=L,B=B,J_min=J_min,maxscale=maxscale,nmaps=nmaps,binsave=binsave)
    if nproc > 1:
        os.system(f"mpiexec -n {nproc} python random_realisations.py {' '.join(infiles)} {L} {B} {J_min} {maxscale} {nmaps} {binsave}")

if __name__=='__main__':
    process()

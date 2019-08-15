import numpy as np
import healpy as hp
import pys2let
# import cy_mass_mapping as mm
import sys, os, time
from struct import *
from contextlib import contextmanager
from mpi4py import MPI
from .__init__ import get_data

@contextmanager
def suppress_stdout():
    '''
    Suppresses stdout from some healpy functions
    '''
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

class Params:
    def __init__(self,Nside=32,L=35,B=1.5,J_min=2,maxscale=6,nmaps=500,binsave=True):
        '''     
        Inputs: Nside     = Healpix nside parameter
                L         = maximum angular order
                B         = wavelet parameter
                J_min     = minimum wavelet scale
                maxscale  = maximum scale for which the original is kept
                nmaps     = number of desired random maps
                nscales   = number of wavelet scales in decomposition
                binsave   = if True, save S2N in binary files, if False save as             text
        '''
        self.Nside = Nside
        self.L = L
        self.B = B
        self.J_min = J_min
        self.maxscale = maxscale
        self.nmaps = nmaps
        J=pys2let.pys2let_j_max(B,L,J_min)
        self.nscales = J-J_min+1
        self.binsave = binsave

class RandomMaps:
    def __init__(self,f,f_scal_lm,f_wav_lm,cl,params):
        '''
        Inputs: f         = the original map
                f_scal_lm = the scaling function in harmonic space
                f_wav_lm  = the wavelet coefficients in harmonic space
                cl        = the power spectra of the wavelet scales
        '''
        self.f = f
        self.f_wav_lm = f_wav_lm
        self.f_scal_lm = f_scal_lm
        self.cl = cl
        self.Nside = params.Nside
        self.L = params.L
        self.B = params.B
        self.J_min = params.J_min
        self.maxscale = params.maxscale
        self.nmaps = params.nmaps
        self.nscales = params.nscales

    def hp_lm2ind(self,el,em):
        return em*(2*self.L-1-em)/2+el

    def generate_kappa_lm_hp(self,cl):
        '''
        Generates the lm of a random map (k) based on some power spectrum (cl)
        '''
        k_lm  = np.empty((L*(L+1)/2,), dtype=complex)
        k_lm[self.hp_lm2ind(0, 0, self.L)] = 0.0
        k_lm[self.hp_lm2ind(1, 0, self.L)] = 0.0
        k_lm[self.hp_lm2ind(1, 1, self.L)] = 0.0
        for el in range(2,self.L):
            index = self.hp_lm2ind(el,0)
            k_lm[index] = np.random.randn()*sqrt(cl[el])
            for em in range(1,el+1):
                index = self.hp_lm2ind(el,em)
                k_lm[index] = (np.random.rand()+1j*np.random.randn())*sqrt(cl[el]*0.5)
        return k_lm

    def gen_random_fields(self):
        '''
        Generates the lm of a random map (k) based on the power spectrum (cl) of the original scales to be simulated
        '''
        k_lm = np.zeros((self.L*(self.L+1)//2,self.nscales-self.maxscale),dtype=complex)
        for i,j in enumerate(range(self.maxscale,self.nscales)):
            k_lm[:,i] = generate_kappa_lm_hp(np.ascontiguousarray(self.cl[:,j]))
        self.klm = k_lm

    def make_random_map(self):
        '''
        Makes a random map
        '''
        self.gen_random_fields()
        rand_wav_lm = np.concatenate([self.f_wav_lm[:,0:self.maxscale],self.klm],axis=1)
        frand_lm = pys2let.synthesis_axisym_lm_wav(rand_wav_lm,self.f_scal_lm,self.B,self.L,self.J_min)
        with suppress_stdout():
            frand = hp.alm2map(frand_lm,nside=self.Nside,lmax=self.L-1)
        return frand

    def make_bunch_of_maps(self):
        random_maps = np.zeros((self.nmaps+1,hp.nside2npix(self.Nside)))
        for i in range(self.nmaps):
            random_maps[i] = self.make_random_map()
            print(f'   {i}/{self.nmaps}',end='\r')
        random_maps[self.nmaps] = self.f
        return random_maps

class Stats:
    '''
    Functions for summary statistics and S2N on maps
    '''
    def __init__(self,random_maps,params):
        self.maps = random_maps
        self.nmaps = params.nmaps+1
        self.str_format = f'{self.nmaps}d'
        self.binsave = params.binsave

    def error_map(self):
        self.error = (self.maps).std(axis=0)

    def calc_s2n(self,map,error):
        return (map/error).mean()

    def global_s2n(self,save_append=''):
        self.error_map()
        glob_s2n = np.asarray([self.calc_s2n(self.maps[i],self.error) for i in range(self.nmaps)])
        if self.binsave:
            packed = pack(self.str_format,*glob_s2n)
            with open(f'outputs/global_{save_append}','bw') as file:
                file.write(bytes(packed))  
        else:
            np.savetxt(f'outputs/global_{save_append}',glob_s2n)


    def local_s2n(self,save_append=''):
        '''
        save_append = string to append to end of file name
        '''
        locs = [f'tile_{i:04d}' for i in range(1,1105)]
        for loc in locs:
            print(f'   {loc}',end='\r')
            mask = hp.read_map(get_data(f'{loc}.fits'),verbose=False)
            maps_masked = hp.ma(self.maps)
            maps_masked.mask = mask
            loc_sd_map = maps_masked.std(axis=0)
            np.ma.set_fill_value(loc_sd_map,hp.UNSEEN)
            loc_s2n = np.asarray([self.calc_s2n(maps_masked[i][mask!=1],loc_sd_map[mask!=1]) for i in range(self.nmaps)])
            if self.binsave:
                packed = pack(self.str_format,*loc_s2n)
                with open(f'outputs/{loc}_{save_append}','bw') as file:
                    file.write(bytes(packed))
            else:
                np.savetxt(f'outputs/{loc}_{save_append}',loc_s2n)

def open_map(file):
    '''
    Reads fits file containing a HealPix map.
    Returns map in real space and Nside parameter
    '''
    f = hp.read_map(file,verbose=False)
    Nside = hp.get_nside(f)
    return f, Nside

def wavelet_decomp(f,params):
    '''
    Performs the wavelet transform of the input map f
    '''
    Nside = params.Nside
    L = params.L
    B = params.B
    J_min = params.J_min
    maxscale = params.maxscale
    nscales = params.nscales
    with suppress_stdout():
        flm = hp.map2alm(f,lmax=L-1)
    f_wav_lm, f_scal_lm = pys2let.analysis_axisym_lm_wav(flm,B,L,J_min)
    f_wav = np.zeros([hp.nside2npix(Nside), nscales])
    cl = np.zeros([L,nscales])
    for j in range(maxscale,nscales):
        with suppress_stdout():
            f_wav[:,j] = hp.alm2map(f_wav_lm[:,j].ravel(),nside=Nside,lmax=L-1)
            cl[:,j] = hp.anafast(f_wav[:,j],lmax=L-1)
    return f_scal_lm, f_wav_lm, cl



def run(infile,L=35,B=1.5,J_min=2,maxscale=6,nmaps=500,binsave=True,save_append=1):
    print(f'   READING INFILE...')
    f,Nside = open_map(infile)

    print(f'   SETTING PARAMETERS...')
    params = Params(Nside,L,B,J_min,maxscale,nmaps,binsave)

    print(f'   WAVELET DECOMPOSITION...')
    f_scal_lm, f_wav_lm, cl = wavelet_decomp(f,params)

    print(f'   MAKING RANDOM MAPS...')
    maps = RandomMaps(f,f_scal_lm,f_wav_lm,cl,params)
    bunch = maps.make_bunch_of_maps()

    print(f'   CALCULATING GLOBAL S2N...')
    stats = Stats(bunch,params)
    stats.global_s2n(save_append)

    print(f'   CALCULATING LOCAL S2N...')
    stats.local_s2n(save_append)

def run_par(infiles,L=35,B=1.5,J_min=2,maxscale=6,nmaps=500,binsave=True):
    nfiles = len(infiles)
    comm = MPI.COMM_WORLD
    # comm = MPI.Comm.Get_parent()
    rank = comm.Get_rank()
    size = comm.Get_size()
    for i in range(nfiles):
        if i%size != rank:
            continue
        print(f'   File {i+1} being done by processor {rank+1} of {size}' )
        sys.stdout.flush()

        print(f'      proc {rank+1}: READING INFILE...')
        sys.stdout.flush()
        infile = infiles[i]
        f,Nside = open_map(infile)

        params = Params(Nside,L,B,J_min,maxscale,nmaps,binsave)

        print(f'      proc {rank+1}: WAVELET DECOMPOSITION...')
        sys.stdout.flush()
        f_scal_lm, f_wav_lm, cl = wavelet_decomp(f,params)

        print(f'      proc {rank+1}: MAKING RANDOM MAPS...')
        sys.stdout.flush()
        maps = RandomMaps(f,f_scal_lm,f_wav_lm,cl,params)
        bunch = maps.make_bunch_of_maps()

        print(f'      proc {rank+1}: CALCULATING GLOBAL S2N...')
        sys.stdout.flush()
        stats = Stats(bunch,params)
        s2n = stats.global_s2n(save_append=f'{i+1}')

        print(f'      proc {rank+1}: CALCULATING LOCAL S2N...')
        sys.stdout.flush()
        stats.local_s2n(save_append=f'{i+1}')

        print(f'   File {i+1} done. Processor {rank+1} moving on...' )
        sys.stdout.flush()

    print(f'   Processor {rank+1} finished')
    sys.stdout.flush()

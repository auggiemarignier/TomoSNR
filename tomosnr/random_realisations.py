import numpy as np
import healpy as hp
import pys2let
import sys
import os
from struct import pack
from contextlib import contextmanager
from joblib import Parallel, delayed
from .__init__ import get_data


@contextmanager
def suppress_stdout():
    """
    Suppresses stdout from some healpy functions
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout


class Params:
    def __init__(
        self,
        Nside=32,
        L=35,
        B=1.5,
        J_min=2,
        simscales=[-1],
        nmaps=500,
        tilesize=8,
        binsave=True,
        par=True,
        locsonly=False,
    ):
        """
        Inputs: Nside     = Healpix nside parameter
                L         = maximum angular order
                B         = wavelet parameter
                J_min     = minimum wavelet scale
                simscales = list of scales to simulate - scale 0 is the scaling function
                nmaps     = number of desired random maps
                tilesize  = number of degrees in lat long for mask
                binsave   = if True, save S2N in binary files, if False save as text
                par       = True if running in parallel
                locsonly  = True if running for only specific locations and not tiles
        """
        self.Nside = Nside
        self.L = L
        self.B = B
        self.J_min = J_min
        self.simscales = simscales
        self.nmaps = nmaps
        J = pys2let.pys2let_j_max(B, L, J_min)
        self.nscales = J - J_min + 1
        self.binsave = binsave
        self.par = par
        self.tilesize = tilesize
        self.locsonly = locsonly


class RandomMaps:
    def __init__(self, f, f_scal_lm, f_wav_lm, cl, params):
        """
        Inputs: f         = the original map
                f_scal_lm = the scaling function in harmonic space
                f_wav_lm  = the wavelet coefficients in harmonic space
                cl        = the power spectra of the wavelet scales
        """
        self.f = f
        self.f_wav_lm = f_wav_lm
        self.f_scal_lm = f_scal_lm
        self.cl = cl
        self.Nside = params.Nside
        self.L = params.L
        self.B = params.B
        self.J_min = params.J_min
        self.simscales = params.simscales
        self.nmaps = params.nmaps
        self.nscales = params.nscales
        self.par = params.par
        self.locsonly = params.locsonly

    def hp_lm2ind(self, el, em):
        return int(em * (2 * self.L - 1 - em) / 2 + el)

    def generate_kappa_lm_hp(self, cl):
        """
        Generates the lm of a random map (k) based on some power spectrum (cl)
        """
        k_lm = np.empty((self.L * (self.L + 1) // 2,), dtype=complex)
        k_lm[self.hp_lm2ind(0, 0)] = 0.0
        k_lm[self.hp_lm2ind(1, 0)] = 0.0
        k_lm[self.hp_lm2ind(1, 1)] = 0.0
        for el in range(2, self.L):
            index = self.hp_lm2ind(el, 0)
            k_lm[index] = np.random.randn() * np.sqrt(cl[el])
            for em in range(1, el + 1):
                index = self.hp_lm2ind(el, em)
                k_lm[index] = (np.random.rand() + 1j * np.random.randn()) * np.sqrt(
                    cl[el] * 0.5
                )
        return k_lm

    def gen_random_fields(self):
        """
        Generates the lm of a random map (k) based on the power spectrum (cl) of the original scales to be simulated
        """
        k_lm = np.zeros(
            (self.L * (self.L + 1) // 2, len(self.simscales)), dtype=complex
        )
        for i, j in enumerate(self.simscales):
            k_lm[:, i] = self.generate_kappa_lm_hp(np.ascontiguousarray(self.cl[:, j]))
        return k_lm

    def make_random_map(self):
        """
        Makes a random map
        """
        k_lm = self.gen_random_fields()
        rand_wav_lm = np.copy(self.f_wav_lm)
        for i, s in enumerate(self.simscales):
            rand_wav_lm[:, s] = k_lm[:, i]
        frand_lm = pys2let.synthesis_axisym_lm_wav(
            rand_wav_lm, self.f_scal_lm, self.B, self.L, self.J_min
        )
        with suppress_stdout():
            frand = hp.alm2map(frand_lm, nside=self.Nside, lmax=self.L - 1)
        return frand

    def make_bunch_of_maps(self):
        random_maps = np.zeros((self.nmaps + 1, hp.nside2npix(self.Nside)))
        for i in range(self.nmaps):
            random_maps[i] = self.make_random_map()
            if not self.par:
                print(f"   {i}/{self.nmaps}", end="\r")
        random_maps[self.nmaps] = self.f
        return random_maps


class Stats:
    """
    Functions for summary statistics and S2N on maps
    """

    def __init__(self, random_maps, params, save_summary_maps=True):
        self.maps = random_maps
        self.save_summary_maps = save_summary_maps
        self.nmaps = params.nmaps + 1
        self.str_format = f"{self.nmaps}d"
        self.binsave = params.binsave
        self.tilesize = params.tilesize
        self.par = params.par
        self.locsonly = params.locsonly

    def error_map(self):
        self.error = (self.maps).std(axis=0)

    def mean_map(self):
        self.mean = (self.maps).mean(axis=0)

    def build_summary_maps(self, save_append=""):
        self.error_map()
        self.mean_map()
        if self.save_summary_maps:
            hp.write_map(f"outputs/error_{save_append}.fits", self.error)
            hp.write_map(f"outputs/mean_{save_append}.fits", self.mean)

    def calc_s2n(self, map, error):
        return (map / error).mean()

    def global_s2n(self, save_append=""):
        glob_s2n = np.asarray(
            [self.calc_s2n(self.maps[i], self.error) for i in range(self.nmaps)]
        )
        if self.binsave:
            packed = pack(self.str_format, *glob_s2n)
            with open(f"outputs/global_{save_append}", "bw") as file:
                file.write(bytes(packed))
        else:
            np.savetxt(f"outputs/global_{save_append}", glob_s2n)

    def local_s2n(self, save_append=""):
        """
        save_append = string to append to end of file name
        """
        if not self.locsonly:
            ntiles = len(
                [
                    name
                    for name in os.listdir(get_data(""))
                    if name.split("_")[0] == str(self.tilesize)
                ]
            )
            locs = [f"{self.tilesize}_tile_{i:04d}" for i in range(1, ntiles + 1)]
        else:
            locs = [
                "afar",
                "australia",
                "brazilcoast",
                "canaries",
                "capeverde",
                "comoros",
                "eastpacificrise",
                "everest",
                "greenland",
                "hawaii",
                "iceland",
                "macdonald",
                "marquesas",
                "midatalanticridge",
                "namibia",
                "pitcairn",
                "richardsdeep",
                "russia",
                "samoa",
                "southernocean",
                "tahiti",
                "yellowstone",
            ]
        for loc in locs:
            if not self.par:
                print(f"   {loc}", end="\r")
            mask = hp.read_map(get_data(f"{loc}.fits"), verbose=False)
            maps_masked = hp.ma(self.maps)
            maps_masked.mask = mask
            loc_sd_map = maps_masked.std(axis=0)
            np.ma.set_fill_value(loc_sd_map, hp.UNSEEN)
            loc_s2n = np.asarray(
                [
                    self.calc_s2n(maps_masked[i][mask != 1], loc_sd_map[mask != 1])
                    for i in range(self.nmaps)
                ]
            )
            if self.binsave:
                packed = pack(self.str_format, *loc_s2n)
                with open(f"outputs/{loc}_{save_append}", "bw") as file:
                    file.write(bytes(packed))
            else:
                np.savetxt(f"outputs/{loc}_{save_append}", loc_s2n)


def open_map(file):
    """
    Reads fits file containing a HealPix map.
    Returns map in real space and Nside parameter
    """
    f = hp.read_map(file, verbose=False)
    Nside = hp.get_nside(f)
    return f, Nside


def wavelet_decomp(f, params):
    """
    Performs the wavelet transform of the input map f
    """
    Nside = params.Nside
    L = params.L
    B = params.B
    J_min = params.J_min
    simscales = params.simscales
    nscales = params.nscales
    with suppress_stdout():
        flm = hp.map2alm(f, lmax=L - 1)
    f_wav_lm, f_scal_lm = pys2let.analysis_axisym_lm_wav(flm, B, L, J_min)
    f_wav = np.zeros([hp.nside2npix(Nside), nscales])
    cl = np.zeros([L, nscales])
    for j in simscales:
        with suppress_stdout():
            f_wav[:, j] = hp.alm2map(f_wav_lm[:, j].ravel(), nside=Nside, lmax=L - 1)
            cl[:, j] = hp.anafast(f_wav[:, j], lmax=L - 1)
    return f_scal_lm, f_wav_lm, cl


def run(
    infile,
    L=35,
    B=1.5,
    J_min=2,
    simscales=[-1],
    nmaps=500,
    tilesize=8,
    binsave=True,
    par=False,
    save_append="",
    locsonly=False,
):
    print("   READING INFILE...")
    f, Nside = open_map(infile)

    print("   SETTING PARAMETERS...")
    params = Params(
        Nside, L, B, J_min, simscales, nmaps, tilesize, binsave, par, locsonly=locsonly
    )

    print("   WAVELET DECOMPOSITION...")
    f_scal_lm, f_wav_lm, cl = wavelet_decomp(f, params)

    print("   MAKING RANDOM MAPS...")
    maps = RandomMaps(f, f_scal_lm, f_wav_lm, cl, params)
    bunch = maps.make_bunch_of_maps()

    print("   BUILDING SUMMARY MAPS...")
    stats = Stats(bunch, params)
    stats.build_summary_maps(save_append)

    print("   CALCULATING GLOBAL S2N...")
    stats.global_s2n(save_append)

    print("   CALCULATING LOCAL S2N...")
    stats.local_s2n(save_append)


def run_par(
    infiles,
    nproc=4,
    L=35,
    B=1.5,
    J_min=2,
    simscales=[-1],
    nmaps=500,
    tilesize=8,
    binsave=True,
    save_summary_maps=True,
    locsonly=False,
):
    nfiles = len(infiles)
    Parallel(n_jobs=nproc)(
        delayed(run)(
            infiles[i],
            L=L,
            B=B,
            J_min=J_min,
            simscales=simscales,
            nmaps=nmaps,
            tilesize=tilesize,
            binsave=binsave,
            par=True,
            save_append=i + 1,
            locsonly=locsonly,
        )
        for i in range(nfiles)
    )

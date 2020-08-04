import healpy as hp
import numpy as np
import os


def pixelise(signal, Nside, longs, lats):
    Npix = hp.nside2npix(Nside)
    pixnum = hp.ang2pix(Nside, longs, lats, lonlat=True)
    amap = np.zeros(Npix)
    count = np.zeros(Npix)
    nsample = len(signal)
    for i in range(nsample):
        pix = pixnum[i]
        amap[pix] += signal[i]
        count[pix] += 1.0
    for i in range(Npix):
        if count[i] > 0:
            amap[i] = amap[i] / count[i]
        else:
            amap[i] = hp.UNSEEN
    return amap


def xyz2hp(xyzfile, Nside, outfile=None):
    """
    Takes in a text file with columns (longitude, latitude, values)
    and a desired Healpix Nside
    Writes a Healpix .fits file
    """
    data = np.loadtxt(xyzfile)
    longs = np.array([data[i][0] for i in range(len(data))])
    lats = np.array([data[i][1] for i in range(len(data))])
    vals = np.array([data[i][2] for i in range(len(data))])
    hpmap = pixelise(vals, Nside, longs, lats)

    if outfile is None:
        outfile = os.path.basename(xyzfile).split(".")[0]
    hp.write_map(f"{outfile}.fits", hpmap, overwrite=True)

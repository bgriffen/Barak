""" Calculate virial quantities for a dark matter halo given a
cosmology.
"""
from __future__ import division
from astropy import cosmology
from astropy.utils import isiterable
from astropy.constants.cgs import G, M_sun, kpc, k_B, m_p
from math import pi

from collections import namedtuple

km = 1e5

def deltavir(redshift, cosmo=None):
    """ The Virial overdensity as a function redshift. 

    This is an approximation parameterized by Bryan & Norman 98, ApJ,
    495, 80.  Good to 1% for omega(z) = 0.1-1, requires either omega =
    1 (flat universe) or omega_lambda = 0.

    This is given by dissipationless spherical top-hat models of
    gravitational collapse (Peebles 1990 'The Large Scale structure of
    the Universe', Eke et al. 1996 MNRAS, 282, 263).
    """
    if cosmo is None:
        cosmo = cosmology.get_current()

    if cosmo.Ok0 != 0:
        if cosmo.Ode0 == 0:
            x = cosmo.Om(redshift) - 1
            return 18*pi**2 + 60*x - 32*x**2
        else:
            raise ValueError("Can't compute deltavir for a non-flat cosmology "
                             "with a cosmological constant")
    else:
        x = cosmo.Om(redshift) - 1
        return 18*pi**2 + 82*x - 39*x**2


def calc_virial_values(M, z, cosmo=None, mu=0.59):
    """ Find the virial radius, circular velocity and temperature for
    a dark matter halo at a given mass and redshift.

    Parameters
    ----------
    mass : array_like, shape N
      Total halo mass (including dark matter) in solar masses.
    z : array_like, shape M
      Redshift.
    cosmo : cosmology (optional)
      The cosmology to use.
    mu : float (optional)
      The mean molecular weight. The virial temperature is
      proportional to mu.

    Returns
    -------
    vir : named tuple of ndarrays with shape (N, M)
      The virial radius (proper kpc), circular velocity (km/s) and
      temperature (K). If N or M is 1, that dimension is suppressed.

    Notes
    -----
    The value of mu depends on the ionization fraction of the gas; mu
    = 0.59 for a fully ionized primordial gas (the default), mu = 0.61
    for a gas with ionized hydrogen but only singly ionized helium,
    and mu = 1.22 for neutral primordial gas.

    Examples
    --------
    >>> vir = calc_virial_values(1e12, 0)
    >>> print vir.r, vir.v, vir.T
    261.195728743 128.338776885 588643.476006
    >>> r,v,T = calc_virial_values(1e12, [0.5, 1, 1.5, 2])
    >>> r
    array([ 198.57846074,  156.44358398,  127.91018732,  107.74327378])
    >>> v
    array([ 147.1888328 ,  165.82959995,  183.39536858,  199.82317152])
    >>> T
    array([  774259.0063081 ,   982789.81965216,  1202024.36495813,
           1427014.0148491 ])
    """

    if isiterable(M):
        M = np.asarray(M)

    if cosmo is None:
        cosmo = cosmology.get_current()

    # convert to cgs
    M_g = M * M_sun

    rho_virial = deltavir(z) * cosmo.critical_density(z)

    # deal with cases where we have two input arrays
    if isiterable(M) and isiterable(rho_virial):
        M_g = np.atleast_2d(M_g).T
        rho_virial = np.atleast_2d(rho_virial)

    rvir = ((3 * M_g) / (4 * pi * rho_virial))**(1./3)
    vcirc = (G * M_g / rvir)**0.5
    Tvir = mu * m_p * vcirc**2 / (2 * k_B)

    VirialValues = namedtuple('virial_values', 'r v T')

    return VirialValues(r=rvir/kpc, v=vcirc/km, T=Tvir)

""" Statistics-related functions.
"""

# p2.6+ compatibility
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import numpy as np

def _bisect(func, target, xlo=-10, xhi=10):
    """ Find x value such that func(x) = target.

    Assumes the value is positive and does log bisection.
    """
    if np.isnan([target, xlo, xhi]).any():
        return np.nan, np.nan
    target, xlo, xhi = (float(val) for val in (target, xlo, xhi))

    fmin = lambda x: func(10**x) - target

    dlo = fmin(xlo)
    dhi = fmin(xhi)
    if not np.sign(dlo * dhi) < 0:
        raise ValueError('Min and max x values do not bracket the target')

    if dhi < dlo:
        fmin = lambda x: - (func(10**x) - target)

    n = 0
    while True:
        x = 0.5 * (xlo + xhi)
        diff = fmin(x)
        if abs(diff) < 1e-6:
            break
        if n == 1000:
            raise RuntimeError('Max evaluations reached (1000)')
        elif diff > 0:
            xhi = x
        else:
            xlo = x
        n += 1

    return 10**x

def poisson_min_max_limits(conf, nevents):
    """ Calculate the minimum and maximum mean Poisson value mu
    consistent with seeing nevents at a given confidence level.

    conf: float
      95%, 90%, 68.3% or similar.
    nevents: int
      The number of events observed.

    Returns
    -------
    mulo, mhi : floats
      Mean number of events such that >= observed number of events
      nevents occurs in fewer than conf% of cases (mulo), and mean
      number of events such that <= nevents occurs in fewer than conf%
      of cases (muhi)
    """
    from scipy.stats import poisson
    nevents = int(nevents)
    conf = float(conf)

    if np.isnan(conf) or np.isnan(nevents):
        return np.nan, np.nan
    target = 1 - conf/100.
    if nevents == 0:
        mulo = 0
    else:
        mulo = _bisect(lambda mu: 1 - poisson.cdf(nevents-1, mu), target)

    muhi  = _bisect(lambda mu: poisson.cdf(nevents, mu), target)

    return mulo, muhi

def poisson_confidence_interval(conf, nevents):
    """ Find the Poisson confidence interval.

    Parameters
    ----------
    conf: float
      Confidence level in percent (95, 90, 68.3% or similar).
    nevents: int
      The number of events observed. If 0, then return the
      1-sided upper limit.

    Returns
    -------
    mulo, mhi : floats
      The two-sided confidence interval such that for mulo, >=
      observed number of events occurs in fewer than conf% of cases,
      and for muhi, <= nevents occurs in fewer than conf% of cases.
    """        
    if nevents == 0:
        return poisson_min_max_limits(conf, nevents)
    return poisson_min_max_limits(conf + 0.5*(100-conf), nevents)

def binomial_min_max_limits(conf, ntrial, nsuccess):
    """ Calculate the minimum and maximum binomial probability
    consistent with seeing nsuccess from ntrial at a given confidence level.

    conf: float
      95%, 90%, 68.3% or similar.
    ntrial, nsuccess: int
      The number of trials and successes.

    Returns
    -------
    plo, phi : floats
      Mean number of events such that >= observed number of events
      nevents occurs in fewer than conf% of cases (mulo), and mean
      number of events such that <= nevents occurs in fewer than conf%
      of cases (muhi)
    """
    from scipy.stats import binom
    nsuccess = int(nsuccess)
    ntrial = int(ntrial)
    conf = float(conf)

    if np.isnan(conf):
        return np.nan, np.nan
    target = 1 - conf/100.
    if nsuccess == 0:
        plo = 0
    else:
        plo = _bisect(lambda p: 1 - binom.cdf(nsuccess-1, ntrial, p), target,
                     xhi=0)
    if nsuccess == ntrial:
        phi = 1
    else:
        phi = _bisect(lambda p: binom.cdf(nsuccess, ntrial, p), target,
                     xhi=0)

    return plo, phi

def binomial_confidence_interval(conf, ntrial, nsuccess):
    """ Find the binomial confidence level.

    Parameters
    ----------
    conf: float
      Confidence level in percent (95, 90, 68.3% or similar).
    ntrial: int
      The number of trials.
    nsuccess: int
      The number of successes from the trials. If 0, then return the
      1-sided upper limit.

    Returns
    -------
    plo, phi : floats
      The two-sided confidence interval: probabilities such that >=
      observed number of successes occurs in fewer than conf% of cases
      (plo), and prob such that <= number of success occurs in fewer
      than conf% of cases (phi).
    """
    if nsuccess == 0:
        return binomial_min_max_limits(conf, ntrial, nsuccess)
    return binomial_min_max_limits(conf + 0.5*(100 - conf), ntrial, nsuccess)

def blackbody_nu(nu, T):
    """ Blackbody as a function of frequency (Hz) and temperature (K).

    Parameters
    ----------
    nu : array_like
      Frequency in Hz.

    Returns
    -------
    Jnu : ndarray
      Intensity with units of erg/s/cm^2/Hz/steradian

    See Also
    --------
    blackbody_lam
    """
    from .constants import hplanck, c, kboltz
    return 2*hplanck*nu**3 / (c**2 * (np.exp(hplanck*nu / (kboltz*T)) - 1))

def blackbody_lam(lam, T):
    """ Blackbody as a function of wavelength (Angstroms) and temperature (K).

    Parameters
    ----------
    lam : array_like
      Wavelength in Angstroms.

    Returns
    -------
    Jlam : ndarray
       Intensity with units erg/s/cm^2/Ang/steradian

    See Also
    --------
    blackbody_nu
    """
    from .constants import hplanck, c, kboltz
    # to cm
    lam = lam * 1e-8
    # erg/s/cm^2/cm/sr
    Jlam = 2*hplanck*c**2 / (lam**5 * (np.exp(hplanck*c / (lam*kboltz*T)) - 1))

    # erg/s/cm^2/Ang/sr
    return Jlam * 1e8

def remove_outliers(data, nsig_lo, nsig_hi, method='median',
                    nitermax=100, verbose=False):
    """Strip outliers from a dataset, iterating until converged.

    Parameters
    ----------
      data : 1D numpy array.
        data from which to remove outliers.
      nsigma_lo : float
        limit defining low outliers: number of standard deviations below the
        centre of the data.
      nsigma_hi : float
        limit defining high outliers: number of standard deviations above the
        centre of the data.
      clip : {'low'|'high'|'both'}
        Respectively removes outliers below, above, or on both sides
        of the limits set by nsigma.
      method : {'mean'|'median'|function}
        set central value, or method to compute it.
      nitermax : int
        number of iterations before exit; defaults to 100

    Returns
    -------
    mask : boolean array same shape as data
      This is False wherever there is an outlier.
    """
    # 2009-09-04 13:24 IJC: Created
    # 2009-09-24 17:34 IJC: Added 'retind' feature.  Tricky, but nice!
    # 2009-10-01 10:40 IJC: Added check for stdev==0
    # 2009-12-08 15:42 IJC: Added check for isfinite

    # if a string, use the corresponding numpy function

    data = np.asarray(data).ravel()

    funcs = {'mean': np.mean, 'median': np.median}
    if method in funcs:
        method = funcs[method]

    if clip == 'low':
        def find_good(d, cen, thresh): return d > (cen - thresh)
    elif clip == 'high':
        def find_good(d, cen, thresh): return d < (cen + thresh)
    else:
        def find_good(d, cen, thresh): return np.abs(d) < (cen + thresh)

    good = ~np.isnan(data)
    ngood = good.sum()
    niter = 0
    while ngood > 0:
        d = data[good]
        centre = method(d)
        stdev = d.std()
        if stdev > 0:
            c0 = d > (centre - nsigma_lo * stdev)
            c0 &= d < (centre + nsigma_hi * stdev)
            good[good] = c0

        niter += 1
        ngoodnew = good.sum()
        if ngoodnew == ngood or niter > nitermax:
            break
        if verbose:
            print(i, ngood, ngoodnew)
            print("centre, std", centre, stdev)

        ngood = ngoodnew

    return good

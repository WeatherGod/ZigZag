import numpy as np
from scipy import stats


def jackknife(bootfunc, inputData, *func_args, **func_kwargs) :
    inputData = np.asanyarray(inputData)
    n = inputData.shape[0]
    i = np.arange(n)
    # Produce a grid of index numbers such that each row
    # contains all indices except one.  Each element is skipped once.
    ins = (i[np.newaxis, :-1] - i[:, np.newaxis]) % n
    return np.atleast_2d([bootfunc(inputData[aSamp, ...], *func_args, **func_kwargs)
                         for aSamp in ins])


def bootstrap(N, bootfunc, inputData, *func_args, **func_kwargs) :
    inputData = np.asanyarray(inputData)
    sampIndex = np.random.randint(inputData.shape[0], size=(N, inputData.shape[0]))

    bstat = np.array([bootfunc(inputData[samp, ...], *func_args, **func_kwargs)
                      for samp in sampIndex])
    # Make sure it has at least 2 dims and that the first dim
    # is for the number of times we bootstrapped.
    bstat.shape = (N, -1)
    return bstat

def bootci(N, bootfunc, inputData, alpha=0.5, *func_args, **func_kwargs) :
    stat = np.asanyarray(bootfunc(inputData, *func_args, **func_kwargs))
    bstat = bootstrap(N, bootfunc, inputData, *func_args, **func_kwargs)
    z_0 = fz0(bstat, stat)

    jstat = jackknife(bootfunc, inputData, *func_args, **func_kwargs)
    score = -(jstat-np.mean(jstat, axis=0))
    skew = np.sum(score**3, axis=0)/(np.sum(score**2, axis=0)**1.5)
    acc = skew/6.0

    # transform back with bias corrected and acceleration
    z_alpha1 = stats.norm.ppf(alpha/2.0)
    z_alpha2 = -z_alpha1
    pct1 = np.atleast_1d(100*stats.norm.cdf(z_0 +(z_0+z_alpha1)/(1-acc*(z_0+z_alpha1))))
    pct2 = np.atleast_1d(100*stats.norm.cdf(z_0 +(z_0+z_alpha2)/(1-acc*(z_0+z_alpha2))))

    # inverse of ECDF
    return (np.array([stats.scoreatpercentile(bstat[:, i], pct) for i, pct in enumerate(pct2)]),
            np.array([stats.scoreatpercentile(bstat[:, i], pct) for i, pct in enumerate(pct1)]))



def fz0(bstat, stat) :
    # Bias-corrected z0 constant
    # norm.ppf is the inverse cdf of the normal distribution
    return stats.norm.ppf((np.sum(bstat < stat, axis=0)
                           + np.sum(bstat == stat, axis=0) / 2.0)
                          / float(len(bstat)))

import numpy as np

def MakeErrorBars(bootMeans, bootCIs, ax, label=None, startLoc=0.5,
                  graphType='line', **kwargs) :
    """
    bootCIs[1] is the lower end of the confidence interval
    while bootCIs[0] is the upper end of the confidence interval.

    *graphType* can be either 'line' (default) or 'bar'.
    """
    xlocs = np.arange(len(bootMeans)) + startLoc
    yerr = (bootMeans - bootCIs[1],
            bootCIs[0] - bootMeans)
    error_kw = dict(elinewidth=3.0, capsize=5, markersize=14, mew=3.0)

    if graphType == 'line' :
        kwargs.pop('width', None)
        error_kw.update(kwargs)
        ax.errorbar(xlocs, bootMeans,
                    yerr=yerr, label=label, **error_kw)
    elif graphType == 'bar' :
        error_kw.update(dict(ecolor='k', elinewidth=1.0, mew=1.0))
        ax.bar(xlocs, bootMeans, yerr=yerr, label=label,
               error_kw=error_kw, align='center', **kwargs)


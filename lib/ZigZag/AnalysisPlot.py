import numpy as np

def MakeErrorBars(bootMeans, bootCIs, ax, label=None, startLoc=0.5,
                  fmt='.', graphType='line', width=0.8) :
    """
    bootCIs[1] is the lower end of the confidence interval
    while bootCIs[0] is the upper end of the confidence interval.

    *fmt* is passed to the plotting function.
    *graphType* can be either 'line' (default) or 'bar'.
    *width* is only needed if *graphType* == 'bar'.
    """
    xlocs = np.arange(len(bootMeans)) + startLoc
    yerr = (bootMeans - bootCIs[1],
            bootCIs[0] - bootMeans)
    error_kw = dict(elinewidth=3.0, capsize=5, markersize=14, mew=3.0)

    if graphType == 'line' :
        ax.errorbar(xlocs, bootMeans,
                    yerr=yerr, fmt=fmt, label=label, **error_kw)
    elif graphType == 'bar' :
        error_kw.update(dict(ecolor='k', elinewidth=1.0, mew=1.0))
        ax.bar(xlocs, bootMeans, width=width, yerr=yerr, label=label,
               error_kw=error_kw, align='center')


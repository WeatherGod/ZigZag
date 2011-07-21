import numpy as np

def MakeErrorBars(bootMeans, bootCIs, ax, label=None, startLoc=0.5, fmt='.') :
    """
    bootCIs[1] is the lower end of the confidence interval
    while bootCIs[0] is the upper end of the confidence interval.
    """
    xlocs = np.arange(len(bootMeans)) + startLoc
    ax.errorbar(xlocs, bootMeans, yerr=(bootMeans - bootCIs[1],
                                        bootCIs[0] - bootMeans),
                fmt=fmt, elinewidth=3.0, capsize=5, markersize=14, 
                mew=3.0, label=label)




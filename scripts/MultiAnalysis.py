#!/usr/bin/env python

from AnalyzeTracking import *
import ZigZag.ParamUtils as ParamUtils
import la
import os.path
import numpy as np
import ZigZag.bootstrap as btstrp
from ListRuns import CommonTrackRuns, Sims_of_MultiSim

from multiprocessing import Pool

def _analyze_trackings(simName, multiSim, skillNames, trackRuns, multiDir) :
    dirName = os.path.join(multiDir, simName)
    print "Sim:", simName
    simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName,
                                                             "simParams.conf"))

    analysis = AnalyzeTrackings(simName, simParams, skillNames,
                                trackRuns=trackRuns, path=multiDir)
    analysis = analysis.insertaxis(axis=1, label=simName)
    return analysis
   

def MultiAnalyze(simNames, multiSim, skillNames,
                 trackRuns, path='.') :
    completeAnalysis = None
    multiDir = os.path.join(path, multiSim)

    p = Pool()
           
    # Now, go through each simulation and analyze them.
    results = [p.apply_async(_analyze_trackings, (simName, multiSim, skillNames,
                                                  trackRuns, multiDir)) for
               simName in simNames]

    p.close()
    p.join()

    # FIXME: With the update larrys, this can probably be improved.
    for res in results :
        if completeAnalysis is None :
            completeAnalysis = res.get()
        else :
            completeAnalysis = completeAnalysis.merge(res.get())

    return completeAnalysis

def Bootstrapping(n_boot, ci_alpha, analysisInfo) :
    booting = btstrp.bootstrap(n_boot, np.mean, analysisInfo, axis=0)
    btmean = booting.mean(axis=0)
    btci = btstrp.bootci(n_boot, np.mean, analysisInfo, alpha=ci_alpha, axis=0)

    return btmean, btci



def MakeErrorBars(bootMeans, bootCIs, ax, label=None, startLoc=0.5) :
    """
    bootCIs[1] is the lower end of the confidence interval
    while bootCIs[0] is the upper end of the confidence interval.
    """
    xlocs = np.arange(len(bootMeans)) + startLoc
    ax.errorbar(xlocs,
          bootMeans, yerr=(bootMeans - bootCIs[1],
                           bootCIs[0] - bootMeans),
                  fmt='.', elinewidth=3.0, capsize=5, markersize=14, mew=3.0, label=label)

 
def main(args) :
    from ListRuns import ExpandTrackRuns

    n_boot = 100
    ci_alpha = 0.05

    if args.cacheOnly :
        args.skillNames = []
    else :
        import matplotlib.pyplot as plt

    simNames = Sims_of_MultiSim(args.multiSim, args.directory)
    fullNames = [os.path.join(args.multiSim, aSim) for aSim in simNames]
    commonTrackRuns = CommonTrackRuns(fullNames, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    # Double-check that the generated trackRuns were all available
    # NOTE: The following if-statement should now be obsolete with
    #       the use of ExpandTrackRuns().
    #if not set(commonTrackRuns).issuperset(trackRuns) :
    #    missingRuns = set(trackRuns).difference(commonTrackRuns)
    #    raise ValueError("Not all of the given trackruns were available: %s" % list(missingRuns))

    shortNames = args.labels if args.labels is not None else [runname[-11:] for runname in trackRuns]
    #xlab = 'SCIT: Speed Threshold'
    plotTitles = args.titles if args.titles is not None else args.skillNames

    completeAnalysis = MultiAnalyze(simNames, args.multiSim, args.skillNames,
                                    trackRuns=trackRuns, path=args.directory)

    for skillname, title in zip(args.skillNames, plotTitles) :
        DisplayAnalysis(completeAnalysis.lix[[skillname]], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo=args.compareTo)
        print "\n\n"

        btmean, btci = Bootstrapping(n_boot, ci_alpha, completeAnalysis.lix[[skillname]].x)

        fig = plt.figure(figsize=args.figsize)
        ax = fig.gca()
        
        MakeErrorBars(btmean, btci, ax)
        ax.set_xticks(np.arange(len(btmean)) + 0.5)
        ax.set_xticklabels(shortNames, fontsize='medium')
        ax.set_xlim(0.0, len(shortNames))
        #ax.set_xlabel(xlab)
        ax.set_ylabel('Skill Score')
        ax.set_title(title)

        if args.saveImgFile is not None :
            fig.savefig("%s_%s.%s" % (args.saveImgFile, skillname, args.imageType))

    if not args.cacheOnly and args.doShow:
        plt.show()


if __name__ == "__main__" :
    import argparse     # Command-line parsing
    from ZigZag.zigargs import AddCommandParser




    parser = argparse.ArgumentParser(description='Analyze the tracking results of multiple storm-track simulations')
    AddCommandParser('MultiAnalysis', parser)
    """
    parser.add_argument("multiSim",
                      help="Analyze tracks for MULTISIM",
                      metavar="MULTISIM", default="NewMulti")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM",
                        metavar="DIRNAME", default='.')
    parser.add_argument("-t", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to analyze.  Analyze all runs if none are given",
                        metavar="RUN", default=None)
    parser.add_argument("skillNames", nargs="+",
                        help="The skill measures to use",
                        metavar="SKILL")
    parser.add_argument("--compare", dest="compareTo", type=str,
                        help="Compare other trackers to TRACKER",
                        metavar="TRACKER", default="MHT")
    parser.add_argument("--cache", dest="cacheOnly",
                        help="Only bother with processing for the purpose of caching results.",
                        action="store_true", default=False)
    parser.add_argument("--save", dest="saveImgFile", type=str,
                        help="Save the resulting image using FILESTEM as the prefix. (e.g., saved file will be 'foo/bar_PC.png' for the PC skill scores and suffix of 'foo/bar').  Use --type to control which image format.",
                        metavar="FILESTEM", default=None)
    parser.add_argument("--type", dest="imageType", type=str,
                        help="Image format to use for saving the figures. Default: %(default)s",
                        metavar="TYPE", default='png')
    parser.add_argument("-f", "--figsize", dest="figsize", type=float,
                        nargs=2, help="Size of the figure in inches (width x height). Default: %(default)s",
                        metavar="SIZE", default=(11.0, 5.0))
    parser.add_argument("--noshow", dest="doShow", action = 'store_false',
                        help="To display or not to display...",
                        default=True)
    parser.add_argument("--find_best", dest="doFindBest", action="store_true",
              help="Find the best comparisons.", default=False)
    parser.add_argument("--find_worst", dest="doFindWorst", action = "store_true",
              help="Find the Worst comparisons.", default=False)
    """
    args = parser.parse_args()

    main(args)



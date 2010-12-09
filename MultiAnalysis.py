#!/usr/bin/env python

from AnalyzeTracking import *
import ParamUtils
import la
import os           # for os.sep
import numpy as np
import bootstrap as btstrp


def FindCommonTrackRuns(simCnt, multiDir) :
    allTrackRuns = []

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%.3d" % index
        dirName = multiDir + os.sep + simName
        simParams = ParamUtils.ReadSimulationParams(dirName + os.sep + "simParams.conf")
        allTrackRuns.append(set(simParams['trackers']))

    # Get the intersection of all the sets of trackRuns in each simulation
    return list(set.intersection(*allTrackRuns))


def MultiAnalyze(multiSimParams, skillNames,
                 trackRuns, path='.') :
    completeAnalysis = None
    multiDir = path + os.sep + multiSimParams['simName']

           
    # Now, go through each simulation and analyze them.
    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%.3d" % index
        dirName = multiDir + os.sep + simName
        print "Sim:", simName
        simParams = ParamUtils.ReadSimulationParams(dirName + os.sep + "simParams.conf")

        analysis = AnalyzeTrackings(simName, simParams, skillNames,
                                    trackRuns=trackRuns, path=multiDir)
        analysis = analysis.insertaxis(axis=1, label=simName)
        if completeAnalysis is None :
            completeAnalysis = analysis
        else :
            completeAnalysis = completeAnalysis.merge(analysis)

    return completeAnalysis

def Bootstrapping(n_boot, ci_alpha, analysisInfo) :
    booting = btstrp.bootstrap(n_boot, np.mean, analysisInfo, axis=0)
    btmean = booting.mean(axis=0)
    btci = btstrp.bootci(n_boot, np.mean, analysisInfo, alpha=ci_alpha, axis=0)

    return btmean, btci



def MakeErrorBars(bootMeans, bootCIs, trackRuns, ax) :
    ax.errorbar(np.arange(len(trackRuns)) + 1,
          bootMeans, yerr=numpy.array([bootMeans - bootCIs[0],
                                       bootCIs[1] - bootMeans]),
                  fmt='.', ecolor='k', elinewidth=2.0, capsize=5, markersize=10, color='k')
    ax.set_xticks(np.arange(len(trackRuns)) + 1)
    ax.set_xticklabels(trackRuns, fontsize='medium')
    ax.set_xlim((0.5, len(trackRuns) + 0.5))
 


if __name__ == "__main__" :
    import argparse     # Command-line parsing
    import matplotlib.pyplot as plt
    from ListRuns import ExpandTrackRuns


    parser = argparse.ArgumentParser(description='Analyze the tracking results of multiple storm-track simulations')
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
    parser.add_argument("--find_best", dest="doFindBest", action="store_true",
              help="Find the best comparisons.", default=False)
    parser.add_argument("--find_worst", dest="doFindWorst", action = "store_true",
              help="Find the Worst comparisons.", default=False)

    args = parser.parse_args()

    n_boot = 100
    ci_alpha = 0.05

    multiDir = args.directory + os.sep + args.multiSim
    paramFile = multiDir + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)


    commonTrackRuns = FindCommonTrackRuns(multiSimParams['simCnt'], multiDir)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    # Double-check that the generated trackRuns were all available
    # NOTE: The following if-statement should now be obsolete with
    #       the use of ExpandTrackRuns().
    #if not set(commonTrackRuns).issuperset(trackRuns) :
    #    missingRuns = set(trackRuns).difference(commonTrackRuns)
    #    raise ValueError("Not all of the given trackruns were available: %s" % list(missingRuns))

    # If there was any expansion, then we probably want to sort these.
    # The idea being that if the user specified which trackers to use, then
    # he probably wants it in the order that he gave it in, otherwise sort it.
    if (args.trackRuns is not None) and (len(args.trackRuns) != len(trackRuns)) :
        trackRuns.sort()
 
    completeAnalysis = MultiAnalyze(multiSimParams, args.skillNames,
                                    trackRuns=trackRuns, path=args.directory)

    trackRuns = completeAnalysis.label[-1]
    shortNames = [runname[-11:] for runname in trackRuns]

    for skillname in args.skillNames :
        DisplayAnalysis(completeAnalysis.lix[[skillname]], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo=args.compareTo)
        print "\n\n"

        btmean, btci = Bootstrapping(n_boot, ci_alpha, completeAnalysis.lix[[skillname]].x)

        fig = plt.figure()
        ax = fig.gca()
        
        MakeErrorBars(btmean, btci, shortNames, ax=ax)
        
    plt.show()

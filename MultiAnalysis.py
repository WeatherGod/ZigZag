#!/usr/bin/env python

from AnalyzeTracking import *
import ParamUtils
import la

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
                 trackRuns=None, path='.') :
    completeAnalysis = None
    multiDir = path + os.sep + multiSimParams['simName']

    # First, find the trackruns that exist for all the simulations
    commonTrackRuns = FindCommonTrackRuns(multiSimParams['simCnt'], multiDir)

    # If the user did not specify a list of trackRuns, then do all of them.
    if trackRuns is None :
        trackRuns = commonTrackRuns

    trackRuns = ExpandTrackRuns(commonTrackRuns, trackRuns)
    
    # Double-check that the given trackRuns are all available
    if not set(commonTrackRuns).issuperset(trackRuns) :
        missingRuns = set(trackRuns).difference(commonTrackRuns)
        raise ValueError("Not all of the given trackruns were available: %s" % list(missingRuns))
        
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
 


if __name__ == "__main__" :
    import argparse     # Command-line parsing
    import os           # for os.sep



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

    multiDir = args.directory + os.sep + args.multiSim
    paramFile = multiDir + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    completeAnalysis = MultiAnalyze(multiSimParams, args.skillNames,
                                    trackRuns=args.trackRuns, path=args.directory)

    for skillname in args.skillNames :
        DisplayAnalysis(completeAnalysis.lix[[skillname]], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo=args.compareTo)
        print "\n\n"
       

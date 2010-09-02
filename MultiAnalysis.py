#!/usr/bin/env python

from AnalyzeTracking import *
import ParamUtils
import la

def MultiAnalyze(multiSimParams, skillNames, path='.') :
    completeAnalysis = None

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%.3d" % index
        dirName = path + os.sep + multiSimParams['simName'] + os.sep + simName
        print "Sim:", simName
        simParams = ParamUtils.ReadSimulationParams(dirName + os.sep + "simParams.conf")



        analysis = AnalyzeTrackings(simName, simParams, skillNames)
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
    parser.add_argument("simName",
                      help="Analyze tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
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

    paramFile = args.simName + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    completeAnalysis = MultiAnalyze(multiSimParams, args.skillNames)

    for skillname in args.skillNames :
        DisplayAnalysis(completeAnalysis.lix[[skillname]], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo=args.compareTo)
        print "\n\n"
       

#!/usr/bin/env python

from AnalyzeTracking import *
import ParamUtils
import la

def MultiAnalyze(multiSimParams, skillcalcs) :
    completeAnalysis = None

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%s%s%.3d" % (multiSimParams['simName'],
                                os.sep, index)
        print "Sim:", simName
        simParams = ParamUtils.ReadSimulationParams(simName + os.sep + "simParams.conf")



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
    parser.add_argument("--find_best", dest="doFindBest", action="store_true",
              help="Find the best comparisons.", default=False)
    parser.add_argument("--find_worst", dest="doFindWorst", action = "store_true",
              help="Find the Worst comparisons.", default=False)

    args = parser.parse_args()

    skillNames = ['HSS', 'TSS', 'Dur']
    compareTo = 'MHT'

    paramFile = args.simName + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    completeAnalysis = MultiAnalyze(multiSimParams, skillNames)

    for skillname in skillNames :
        DisplayAnalysis(completeAnalysis.lix[[skillname]], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo=compareTo)
        print "\n\n"
       

#!/usr/bin/env python

from AnalyzeTracking import *
import ParamUtils
import Analyzers

def MultiAnalyze(multiSimParams, skills) :
    completeAnalysis = {}

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%s%s%.3d" % (multiSimParams['simName'],
                                os.sep, index)
        print "Sim:", simName
        simParams = ParamUtils.ReadSimulationParams(simName + os.sep + "simParams.conf")

        for skillcalc, skillname in skills :
            if skillname not in completeAnalysis :
                completeAnalysis[skillname] = {}

            analysis = AnalyzeTrackings(simName, simParams, skillcalc)
            for tracker in analysis :
                if tracker not in completeAnalysis[skillname] :
                    completeAnalysis[skillname][tracker] = []

                completeAnalysis[skillname][tracker].extend(analysis[tracker])

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

    paramFile = args.simName + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    completeAnalysis = MultiAnalyze(multiSimParams,
                                    [(Analyzers.CalcHeidkeSkillScore, 'HSS'),
                                     (Analyzers.CalcTrueSkillStatistic, 'TSS'),
                                     (Analyzers.Skill_TrackLen, 'Dur')])

    for skillname in completeAnalysis :
        DisplayAnalysis(completeAnalysis[skillname], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo='MHT')
        print "\n\n"
       

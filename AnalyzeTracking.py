#!/usr/bin/env python

from TrackUtils import *
from TrackFileUtils import *
import numpy


def DisplaySkillScores(skillScores, skillScoreName) :

    print skillScoreName
    print "      " + '  '.join(["%7s" % tracker for tracker in skillScores])
    for (index, vals) in enumerate(zip(*skillScores.values())) :
        print ("%3d.  " % index) + \
              '  '.join(['%7.4f' % aVal for aVal in vals])

    print "-" * (6 + 7*(len(skillScores) - 1) + 7)
    print "AVG   " + '  '.join(['%7.4f' % (sum(skillScores[scores])/len(skillScores[scores]))
                                for scores in skillScores])

def AnalyzeTrackings(simName, simParams, skillCalc) :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(simParams['noisyTrackFile']))
    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

    analysis = {}

    for tracker in simParams['trackers'] :
        (finalTracks, finalFAlarms) = FilterMHTTracks(*ReadTracks(simParams['result_file'] + '_' + tracker))
        trackerAssocSegs = CreateSegments(finalTracks)
        trackerFAlarmSegs = CreateSegments(finalFAlarms)

        truthTable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                     trackerAssocSegs, trackerFAlarmSegs)

        analysis[tracker] = [skillCalc(truthTable)]
        
    return analysis

def DisplayAnalysis(analysis, skillName, doFindBest=True, doFindWorst=True, compareTo=None) :
    DisplaySkillScores(analysis, skillName)

    if doFindBest or doFindWorst :
        if compareTo is None :
            compareTo, skillscores = analysis.popitem()
        else :
            skillscores = analysis.pop(compareTo)

        scoreDiffs = numpy.array(skillscores) - numpy.array(analysis.values())
        indices = numpy.argsort(scoreDiffs, axis=1)

        print "\n Against: ", '  '.join(["%7s" % tracker for tracker in analysis])
        if doFindBest :
            print "Best Run: ", '  '.join(["%7d" % index for index in indices[:, -1]])

        if doFindWorst :
            print "Worst Run:", '  '.join(["%7d" % index for index in indices[:, 0]])
    

if __name__ == '__main__' :
    import argparse
    import os                   # for os.sep
    import ParamUtils


    parser = argparse.ArgumentParser("Analyze the tracking results of a storm-track simulation")
    parser.add_argument("simName", type=str,
                      help="Analyze tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
#    parser.add_argument("--find_best", dest="doFindBest", action="store_true",
#              help="Find the best comparisons.", default=False)
#    parser.add_argument("--find_worst", dest="doFindWorst", action = "store_true",
#              help="Find the Worst comparisons.", default=False)

    args = parser.parse_args()

    simParams = ParamUtils.ReadSimulationParams(args.simName + os.sep + "simParams.conf")

    for skillcalc, skillname in [(CalcHeidkeSkillScore, 'HSS'),
                                 (CalcTrueSkillStatistic, 'TSS')] :
        analysis = AnalyzeTrackings(args.simName, simParams, skillcalc)
        DisplaySkillScores(analysis, skillname)
        print '\n\n'


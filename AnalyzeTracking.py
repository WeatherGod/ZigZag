#!/usr/bin/env python

from TrackUtils import *
from TrackFileUtils import *
import numpy
import Analyzers
from la import larry        # Labeled arrays

def DisplaySkillScores(skillScores, skillScoreName) :

    print skillScoreName
    print "      " + '  '.join(["%7s" % tracker for tracker in skillScores])
    for (index, vals) in enumerate(zip(*skillScores.values())) :
        print ("%3d.  " % index) + \
              '  '.join(['%7.4f' % aVal for aVal in vals])

    print "-" * (6 + 7*(len(skillScores) - 1) + 7)
    print "AVG   " + '  '.join(['%7.4f' % (sum(skillScores[scores])/len(skillScores[scores]))
                                for scores in skillScores])

def AnalyzeTrackings(simName, simParams, skillCalcs) :
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

        for skillCalc, skill in skillCalcs :
            if skill not in analysis :
                analysis[skill] = {}

            analysis[skill][tracker] = [skillCalc(**dict(tracks=finalTracks, falarms=finalFAlarms,
                                              truthTable=truthTable))]
        
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

    args = parser.parse_args()

    simParams = ParamUtils.ReadSimulationParams(args.simName + os.sep + "simParams.conf")

    skillcalcs = [(Analyzers.CalcHeidkeSkillScore, 'HSS'),
                  (Analyzers.CalcTrueSkillStatistic, 'TSS'),
                  (Analyzers.Skill_TrackLen, 'Dur')]
    analysis = AnalyzeTrackings(args.simName, simParams, skillcalcs)
    for skillCalc, skill in skillcalcs :
        DisplaySkillScores(analysis[skill], skill)
        print '\n\n'


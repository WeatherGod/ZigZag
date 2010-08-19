#!/usr/bin/env python

from TrackUtils import *
from TrackFileUtils import *
import numpy
import Analyzers
from la import larry        # Labeled arrays

def DisplaySkillScores(skillScores, skillScoreName) :

    print skillScoreName

    print "      " + '  '.join(["%7s" % tracker for tracker in skillScores.label[-1]])
    #for (index, vals) in enumerate(zip(*skillScores.x)) :
    #    print ("%3d.  " % index) + \
    #          '  '.join(['%7.4f' % aVal for aVal in vals])
    print skillScores.x


    print "-" * (6 + 7*(skillScores.shape[0] - 1) + 7)
    #print "AVG   " + '  '.join(['%7.4f' % sum(scores)/len(scores)
    #                            for scores in skillScores.x])
    print skillScores.mean(axis=0).x

def AnalyzeTrackings(simName, simParams, skillCalcs) :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(simParams['noisyTrackFile']))
    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

    # Initializing the analysis data, which will hold a table of analysis results for
    # this simulation
    analysis = numpy.empty((len(skillCalcs),
                            len(simParams['trackers'])))
    labels = [[skill[1] for skill in skillCalcs],
              simParams['trackers']]
    

    for trackerIndex, tracker in enumerate(simParams['trackers']) :
        (finalTracks, finalFAlarms) = FilterMHTTracks(*ReadTracks(simParams['result_file'] + '_' + tracker))
        trackerAssocSegs = CreateSegments(finalTracks)
        trackerFAlarmSegs = CreateSegments(finalFAlarms)

        truthTable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                     trackerAssocSegs, trackerFAlarmSegs)

        for skillIndex, (skillCalc, skill) in enumerate(skillCalcs) :
            analysis[skillIndex, trackerIndex] = skillCalc(**dict(tracks=finalTracks, falarms=finalFAlarms,
                                                                  truthTable=truthTable))

    return larry(analysis, labels)

def DisplayAnalysis(analysis, skillName, doFindBest=True, doFindWorst=True, compareTo=None) :
    DisplaySkillScores(analysis, skillName)

    if doFindBest or doFindWorst :
        if compareTo is None :
            compareTo = analysis.label[1][0]

        skillscores = analysis.lix[:, [compareTo]]
        theOthers = analysis.keep_label('!=', compareTo, axis=1)

        # Do a numpy-style subtraction
        scoreDiffs = skillscores.x - theOthers.x
        indices = numpy.argsort(scoreDiffs, axis=1)

        print "\n Against: ", '  '.join(["%7s" % tracker for tracker in theOthers.label[1]])
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
        DisplaySkillScores(analysis.lix[[skill]], skill)
        print '\n\n'


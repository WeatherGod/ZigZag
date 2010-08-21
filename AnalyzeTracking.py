#!/usr/bin/env python

from TrackUtils import *
from TrackFileUtils import *
import numpy
import Analyzers
from la import larry        # Labeled arrays

def DisplaySkillScores(skillScores, skillScoreName) :
#    print skillScores

    print skillScoreName

    print "      " + '  '.join(["%7s" % tracker for tracker in skillScores.label[-1]])
    #for (index, vals) in enumerate(zip(*skillScores.x)) :
    #    print ("%3d.  " % index) + \
    #          '  '.join(['%7.4f' % aVal for aVal in vals])
    print skillScores.x


    print "-" * (6 + 7*(skillScores.shape[1] - 1) + 7)
    #print "AVG   " + '  '.join(['%7.4f' % sum(scores)/len(scores)
    #                            for scores in skillScores.x])
    print skillScores.mean(axis=0).x

def AnalyzeTrackings(simName, simParams, skillNames) :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(simParams['noisyTrackFile']))
    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

    # Initializing the analysis data, which will hold a table of analysis results for
    # this simulation
    analysis = numpy.empty((len(skillNames),
                            len(simParams['trackers'])))
    labels = [skillNames, simParams['trackers']]
    

    for trackerIndex, tracker in enumerate(simParams['trackers']) :
        (finalTracks, finalFAlarms) = FilterMHTTracks(*ReadTracks(simParams['result_file'] + '_' + tracker))
        trackerAssocSegs = CreateSegments(finalTracks)
        trackerFAlarmSegs = CreateSegments(finalFAlarms)

        truthTable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                     trackerAssocSegs, trackerFAlarmSegs)

        for skillIndex, skill in enumerate(skillNames) :
            analysis[skillIndex, trackerIndex] = Analyzers.skillcalcs[skill](tracks=finalTracks, falarms=finalFAlarms,
                                                                  truthTable=truthTable)

    return larry(analysis, labels)

def DisplayAnalysis(analysis, skillName, doFindBest=True, doFindWorst=True, compareTo=None) :
    DisplaySkillScores(analysis, skillName)

    if doFindBest or doFindWorst :
        if compareTo is None :
            compareTo = analysis.label[1][0]

        # We separate the skillscores for just the one tracker and
        # the rest of the trackers.  We use keep_label because it
        # doesn't squeeze the results down to a scalar float.
        skillscores = analysis.keep_label('==', compareTo, axis=1)
        theOthers = analysis.keep_label('!=', compareTo, axis=1)

        # Do a numpy-style subtraction (for broadcasting reasons)
        scoreDiffs = skillscores.x - theOthers.x
        # Sort score differences for each tracker 
        indices = numpy.argsort(scoreDiffs, axis=0)

        print "\n Against: ", '  '.join(["%7s" % tracker for tracker in theOthers.label[1]])
        if doFindBest :
            print "Best Run: ", '  '.join(["%7d" % index for index in indices[-1]])

        if doFindWorst :
            print "Worst Run:", '  '.join(["%7d" % index for index in indices[0]])
    

if __name__ == '__main__' :
    import argparse
    import os                   # for os.sep
    import ParamUtils


    parser = argparse.ArgumentParser("Analyze the tracking results of a storm-track simulation")
    parser.add_argument("simName", type=str,
                      help="Analyze tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
    parser.add_argument("skillNames", nargs="+",
                        help="The skill measures to use",
                        metavar="SKILL")

    args = parser.parse_args()

    #skillNames = ['HSS', 'TSS', 'Dur']

    simParams = ParamUtils.ReadSimulationParams(args.simName + os.sep + "simParams.conf")

    analysis = AnalyzeTrackings(args.simName, simParams, args.skillNames)
    analysis = analysis.insertaxis(axis=1, label=args.simName)
    for skill in args.skillNames :
        DisplaySkillScores(analysis.lix[[skill]], skill)
        print '\n\n'


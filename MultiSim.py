#!/usr/bin/env python

from TrackSim import TrackSim
import ParamUtils			# for SaveSimulationParams, SetupParser, ParamsFromOptions
from DoTracking import DoTracking
from TrackFileUtils import *
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), 
					#     CompareSegments(), CalcHeidkeSkillScore()
from optparse import OptionParser
import os				# for os.sep
import random

import numpy



def DisplaySkillScores(skillScores, skillScoreName) :

    print skillScoreName
    # TODO: Currently assumes only MHT and SCIT trackers...
    # NOTE: Also assumes that the larger skill value is "better".
    winCnt = 0
    print "        MHT        SCIT"
    for (index, (val1, val2)) in enumerate(zip(skillScores['MHT'], skillScores['SCIT'])) :
        print "%3d.  %7.4f    %7.4f   %s" % (index, val1, val2, str(val1 > val2))
        if val1 > val2 : winCnt += 1

    print "-------------------------------"
    print "      %7.4f    %7.4f   %5.3f" % (sum(skillScores['MHT'])/len(skillScores['MHT']),
					    sum(skillScores['SCIT'])/len(skillScores['SCIT']),
					    float(winCnt) / len(skillScores['MHT']))





parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName", type = "string",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")
parser.add_option("-n", "--num", dest="simCnt", type = "int",
		  help="Repeat Simulation N times.",
		  metavar="N", default=1)
parser.add_option("--find_best", dest="doFindBest", action="store_true",
		  help="Find the best comparisons.", default=False)
parser.add_option("--find_worst", dest="doFindWorst", action = "store_true",
		  help="Find the Worst comparisons.", default=False)


ParamUtils.SetupParser(parser)

(options, args) = parser.parse_args()

if options.simCnt <= 0 :
    parser.error("ERROR: Invalid N value: %d" % (options.simCnt))


hss = {'SCIT': [], 'MHT': []}
tss = {'SCIT': [], 'MHT': []}
checkSumProblem = {'SCIT': [], 'MHT': []}

for index in range(0, options.simCnt) :
    simName = options.simName + ("%s%.3d" % (os.sep, index))
    simParams = ParamUtils.ParamsFromOptions(options, simName = simName)

    if (not os.path.exists(simName)) :
        os.makedirs(simName)

    ParamUtils.SaveSimulationParams(os.sep.join([simName, 'simParams.conf']), simParams)
    theSimulation = TrackSim(simParams, simName)

    SaveTracks(simParams['simTrackFile'], theSimulation['true_tracks'], theSimulation['true_falarms'])
    SaveTracks(simParams['noisyTrackFile'], theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
    SaveCorners(simParams['inputDataFile'], simParams['corner_file'], simParams['frameCnt'], theSimulation['noisy_volumes'])

    simParams['ParamFile'] = os.sep.join([simName, "Parameters"])

    true_AssocSegs = CreateSegments(theSimulation['noisy_tracks'])
    true_FAlarmSegs = CreateSegments(theSimulation['noisy_falarms'])


    for aTracker in simParams['trackers'] :
	DoTracking(aTracker, simParams)
        (finalTracks, finalFAlarms) = ReadTracks(simParams['result_file'] + '_' + aTracker)
        (finalTracks, finalFAlarms) = FilterMHTTracks(finalTracks, finalFAlarms)
        
        trackerAssocSegs = CreateSegments(finalTracks)
	trackerFAlarmSegs = CreateSegments(finalFAlarms)

        truthTable = CompareSegments(true_AssocSegs, true_FAlarmSegs, 
				     trackerAssocSegs, trackerFAlarmSegs)
        """
        # Margin Sums
        #a = len(truthTable['assocs_Correct']['xLocs']) + len(truthTable['assocs_Wrong']['xLocs'])
        b = len(truthTable['falarms_Correct']['xLocs']) + len(truthTable['falarms_Wrong']['xLocs'])
        #c = len(truthTable['assocs_Correct']['xLocs']) + len(truthTable['falarms_Wrong']['xLocs'])
        d = len(truthTable['falarms_Correct']['xLocs']) + len(truthTable['assocs_Wrong']['xLocs'])

        print b, len(finalFAlarms), d, len(theSimulation['noisy_falarms'])

        checkSumProblem[aTracker].append([])

	#if (len(trackerAssocSegs['xLocs']) != a) : checkSumProblem[aTracker][-1].append(1)
	if (len(finalFAlarms) != b) : checkSumProblem[aTracker][-1].append(2)
	#if (len(true_AssocSegs['xLocs']) != c) : checkSumProblem[aTracker][-1].append(3)
	if (len(theSimulation['noisy_falarms']) != d) : checkSumProblem[aTracker][-1].append(4)
        """
        
        hss[aTracker].append(CalcHeidkeSkillScore(truthTable))
        tss[aTracker].append(CalcTrueSkillStatistic(truthTable))



DisplaySkillScores(hss, "HSS")
print "\n"
DisplaySkillScores(tss, "TSS")
"""
print "\n CheckSum Results"
for (index, (mhtResult, scitResult)) in enumerate(zip(checkSumProblem['MHT'], checkSumProblem['SCIT'])) :
    print "%.3d.  %14s %14s" % (index, str(mhtResult), str(scitResult))
"""

# TODO: Yes, I know I am hard-coding the trackers here...
#       I must fix this later.

scoreDiff = numpy.array(hss['MHT']) - numpy.array(hss['SCIT'])
indices = numpy.argsort(scoreDiff, axis=0)

if options.doFindBest :
    print "Best Run:  ", indices[-1]

if options.doFindWorst :
    print "Worst Run: ", indices[0]


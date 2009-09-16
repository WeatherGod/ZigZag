#!/usr/bin/env python

from TrackSim import TrackSim
from SimUtils import *			# for SaveSimulationParams, SetupSimParser,
					# ParamsFromOptions
from DoTracking import DoTracking
from TrackFileUtils import *
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), 
					#     CompareSegments(), CalcHeidkeSkillScore()
from optparse import OptionParser
import os				# for os.sep.join()
import random


parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName", type = "string",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")
parser.add_option("-n", "--num", dest="simCnt", type = "int",
		  help="Repeat Simulation N times.",
		  metavar="N", default=1)
SetupParser(parser)

(options, args) = parser.parse_args()

if options.simCnt <= 0 :
    parser.error("ERROR: Invalid N value: %d" % (options.simCnt))

"""
simParams = dict(corner_filestem = os.sep.join(["%s", "corners"]),
                 inputDataFile = os.sep.join(["%s", "InDataFile"]),
                 simTrackFile = os.sep.join(["%s", "true_tracks"]),
                 noisyTrackFile = os.sep.join(["%s", "noise_tracks"]),
                 result_filestem = os.sep.join(["%s", "testResults"]),
                 frameCnt = 12,
                 totalTracks = 30,
                 speed_variance = 1.5,
                 mean_dir = 50.0,
                 angle_variance = 20.0,
                 endTrackProb = 0.1,
                 xLims = [0., 255.],
                 yLims = [0., 255.],
                 speedLims = [5, 25],
                 false_merge_dist = 15.,
                 false_merge_prob = 0.,
		 #theSeed = 16315
                 theSeed = random.randint(0, 99999)
                )
"""

#simParams['tLims'] = [1, simParams['frameCnt']]
#print "The Seed: ", simParams['theSeed']





theTrackers = ("MHT", "SCIT")

skillScores = {'MHT': [], 'SCIT': []}

for index in range(0, options.simCnt) :
    
    simName = options.simName + ("%s%.3d" % (os.sep, index))
    simParams = ParamsFromOptions(options, simName = simName)

    if (not os.path.exists(simName)) :
        os.makedirs(simName)


    SaveSimulationParams(os.sep.join([simName, 'simParams.txt']), simParams)
    """
    simParams_mod = simParams.copy()
    for aKey in ('simTrackFile', 'inputDataFile', 'corner_filestem', 'noisyTrackFile', 'result_filestem') :
	simParams_mod[aKey] = simParams_mod[aKey] % (simName)
    """
    
    TrackSim(simParams, simName)

    DoTracking(simParams, simName)
    (true_tracks, true_falarms) = ReadTracks(simParams['noisyTrackFile'])
    true_segs = CreateSegments(true_tracks['tracks'], true_falarms)

    for aTracker in theTrackers :
        (finalTracks, finalFAlarms) = ReadTracks(simParams['result_filestem'] + '_' + aTracker)
        (finalTracks, finalFAlarms) = FilterMHTTracks(finalTracks, finalFAlarms)
        
        trackerSegs = CreateSegments(finalTracks, finalFAlarms)

        truthTable = CompareSegments(true_segs, true_falarms, trackerSegs, finalFAlarms)

        skillScores[aTracker].append(CalcHeidkeSkillScore(truthTable))

winCnt = 0
print "  MHT        SCIT"
for (val1, val2) in zip(skillScores['MHT'], skillScores['SCIT']) :
    print "%7.4f    %7.4f   %s" % (val1, val2, str(val1 > val2))
    if val1 > val2 : winCnt += 1

print "------------------------"
print "%7.4f    %7.4f    %5.3f" % (sum(skillScores['MHT'])/options.simCnt,
				   sum(skillScores['SCIT'])/options.simCnt,
				   float(winCnt) / options.simCnt)


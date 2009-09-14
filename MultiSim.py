#!/usr/bin/env python

from TrackSim import TrackSim
from DoTracking import DoTracking
from TrackFileUtils import *
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), 
					#     CompareSegments(), CalcHeidkeSkillScore()
from optparse import OptionParser
import os				# for os.sep.join()
import random


parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")
parser.add_option("-n", "--num", dest="simCnt",
		  help="Repeat Simulation N times.",
		  metavar="N", default=1)

(options, args) = parser.parse_args()

options.simCnt = int(options.simCnt)

if options.simCnt <= 0 :
    print "ERROR: Invalid count: %d" % (options.simCnt)


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
                 false_merge_prob = 0.3,
		 #theSeed = 12345
                 theSeed = random.randint(0, 99999)
                )

simParams['tLims'] = [1, simParams['frameCnt']]
print "The Seed: ", simParams['theSeed']

random.seed(simParams['theSeed'])

theTrackers = ("MHT", "SCIT")

skillScores = {'MHT': [], 'SCIT': []}

for index in range(0, options.simCnt) :
    simName = options.simName + ("_%.3d" % (index))
    simParams_mod = simParams.copy()
    for aKey in ('simTrackFile', 'inputDataFile', 'corner_filestem', 'noisyTrackFile', 'result_filestem') :
	simParams_mod[aKey] = simParams_mod[aKey] % (simName)
    
    TrackSim(simParams_mod, simName)
    DoTracking(simParams_mod, simName)
    (true_tracks, true_falarms) = ReadTracks(simParams_mod['noisyTrackFile'])
    true_segs = CreateSegments(true_tracks['tracks'], true_falarms)

    for aTracker in theTrackers :
        (finalTracks, finalFAlarms) = ReadTracks(simParams_mod['result_filestem'] + '_' + aTracker)
        (finalTracks, finalFAlarms) = FilterMHTTracks(finalTracks, finalFAlarms)
        
        trackerSegs = CreateSegments(finalTracks, finalFAlarms)

        truthTable = CompareSegments(true_segs, true_falarms, trackerSegs, finalFAlarms)

        skillScores[aTracker].append(CalcHeidkeSkillScore(truthTable))

print "MHT:\n"
print skillScores['MHT']

print "\n\nSCIT:\n"
print skillScores['SCIT']

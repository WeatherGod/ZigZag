#!/usr/bin/env python

import random
from TrackFileUtils import *		# for writing the track data
from TrackUtils import *		# for ClipTracks(), CreateVolData(), and CleanupTracks()
from SimUtils import *			# for SaveSimulationParams()
import numpy
import copy				# for deep copying
import math				# for cos(), sin(), and pi

from optparse import OptionParser	# Command-line parsing
import os				# for os.sep.join(), os.mkdir(), os.access()



def IncrementPoint(dataPoint, deltaT, pos_noise, speed_noise) :
    return({'time': dataPoint['time'] + deltaT,
            'pos': [dataPoint['pos'][0] + (dataPoint['speed'][0] * deltaT) + random.uniform(-pos_noise, pos_noise),
                    dataPoint['pos'][1] + (dataPoint['speed'][1] * deltaT) + random.uniform(-pos_noise, pos_noise)],
            'speed': [dataPoint['speed'][0] + random.uniform(-speed_noise, speed_noise),
                      dataPoint['speed'][1] + random.uniform(-speed_noise, speed_noise)]})




def TracksGenerator(trackCnt, tLims, xLims, yLims, speedLims,
		    speed_variance, meanAngle, angle_variance, prob_track_ends) :
    return([MakeTrack(tLims, (meanAngle - angle_variance, meanAngle + angle_variance),
		      speedLims, speed_variance, prob_track_ends, 
		      xLims, yLims) for index in range(trackCnt)])


def MakePoint(tLims, xLocLims, yLocLims, angleLims, speedLims) :
    speed = random.uniform(min(speedLims), max(speedLims))
    angle = random.uniform(min(angleLims), max(angleLims)) * (math.pi / 180.0)
    return({'time': random.randrange(min(tLims), max(tLims)),
	    'pos': [random.uniform(min(xLocLims), max(xLocLims)),
		    random.uniform(min(yLocLims), max(yLocLims))],
	    'speed': [speed * math.cos(angle),
		      speed * math.sin(angle)]})


def MakeTrack(tLims, angleLims, speedLims,
	      speed_variance, prob_track_ends, 
	      xLims, yLims) :
    aPoint = MakePoint(tLims, xLims, yLims, angleLims, speedLims)
    aTrack = {'frameNums': [aPoint['time']],
              'xLocs': [aPoint['pos'][0]], 
	      'yLocs': [aPoint['pos'][1]],
              'xSpeeds': [aPoint['speed'][0]], 
	      'ySpeeds': [aPoint['speed'][1]]}

    
    while (random.uniform(0, 1) > prob_track_ends and aPoint['time'] < max(tLims)) :
        aPoint = IncrementPoint(aPoint, 1, 1.15, speed_variance)
        aTrack['frameNums'].append(aPoint['time'])
	aTrack['xLocs'].append(aPoint['pos'][0])
	aTrack['yLocs'].append(aPoint['pos'][1])
	aTrack['xSpeeds'].append(aPoint['speed'][0])
	aTrack['ySpeeds'].append(aPoint['speed'][1])

    return(aTrack)


def DisturbTracks(true_tracks, true_falarms, true_volData, noise_params) :
    
    tracks = copy.deepcopy(true_tracks)
    falarms = copy.deepcopy(true_falarms)
    volData = copy.deepcopy(true_volData)

    for (volIndex, aVol) in enumerate(volData) :
        xLocs = numpy.array([stormCell['xLoc'] for stormCell in aVol['stormCells']])
	yLocs = numpy.array([stormCell['yLoc'] for stormCell in aVol['stormCells']])
        distMatrix = numpy.hypot(numpy.tile(xLocs, (len(xLocs), 1)) - numpy.rollaxis(numpy.tile(xLocs, (len(xLocs), 1)), 1),
                                 numpy.tile(yLocs, (len(xLocs), 1)) - numpy.rollaxis(numpy.tile(yLocs, (len(xLocs), 1)), 1))

        
	for index1 in range(len(aVol['stormCells'])) :
	    for index2 in range(index1 + 1, len(aVol['stormCells'])) :
		if (distMatrix[index1, index2] <= noise_params['false_merge_dist'] and
		          random.uniform(0, 1) * (distMatrix[index1, index2] / noise_params['false_merge_dist']) < noise_params['false_merge_prob']) :
		    print "\nWe have Occlusion!\n"
		    trackID = aVol['stormCells'][index1]['trackID']
		    strmID = tracks[trackID]['frameNums'].index(aVol['volTime'])
		    tracks[trackID]['frameNums'][strmID] = None
		    tracks[trackID]['xLocs'][strmID] = None
		    tracks[trackID]['yLocs'][strmID] = None
		    aVol['stormCells'][index1] = None
		    
		    # No need to continue checking against this one...
		    break
		    

	# rebuild the stormcells list, effectively removing the storms
	# flagged as a false merger.
	volData[volIndex]['stormCells'] = [aStorm for aStorm in aVol['stormCells'] if aStorm is not None]


    # rebuild the tracks list, effectively removing the storms
    # flagged as a false merger
    (tracks, falarms) = CleanupTracks(tracks, falarms)

    return(tracks, falarms, volData)
		    

parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName",
		  help="Generate Tracks for SIMNAME", 
		  metavar="SIMNAME", default="NewSim")

(options, args) = parser.parse_args()

simParams = dict(corner_filestem = os.sep.join([options.simName, "corners"]),
		 inputDataFile = os.sep.join([options.simName, "InDataFile"]),
		 simTrackFile = os.sep.join([options.simName, "true_tracks"]),
		 noisyTrackFile = os.sep.join([options.simName, "noise_tracks"]),
		 result_filestem = os.sep.join([options.simName, "testResults"]),
		 frameCnt = 9,
		 totalTracks = 30,
		 speed_variance = 1.5,
		 mean_dir = 50.0,
		 angle_variance = 30.0,
		 endTrackProb = 0.1,
		 xLims = [0, 255],
		 yLims = [0, 255],
		 speedLims = [5, 25],
		 false_merge_dist = 10.,
		 false_merge_prob = 0.0,
		 #theSeed = 92395
		 theSeed = random.randint(0, 99999))

print simParams

tLims = [1, simParams['frameCnt']]
print "The Seed: ", simParams['theSeed']

random.seed(simParams['theSeed'])


true_tracks = TracksGenerator(simParams['totalTracks'], tLims, simParams['xLims'], simParams['yLims'],
			      simParams['speedLims'], simParams['speed_variance'], simParams['mean_dir'], 
			      simParams['angle_variance'], simParams['endTrackProb'])
true_falarms = []
(fake_tracks, fake_falarms) = ClipTracks(true_tracks, true_falarms, simParams['xLims'], simParams['yLims'], tLims)
volume_data = CreateVolData(fake_tracks, fake_falarms, tLims, simParams['xLims'], simParams['yLims'])
(fake_tracks, fake_falarms, fake_volData) = DisturbTracks(fake_tracks, fake_falarms, volume_data, 
							  {'false_merge_dist': simParams['false_merge_dist'], 
							   'false_merge_prob': simParams['false_merge_prob']})
#(fake_tracks, fake_falarms) = ClipTracks(fake_tracks, fake_falarms, simParams['xLims'], simParams['yLims'], tLims)

if (not os.access(options.simName, os.F_OK)) :
    os.mkdir(options.simName)

SaveSimulationParams(os.sep.join([options.simName, "simParams"]), simParams)


SaveTracks(simParams['simTrackFile'], true_tracks, true_falarms)
SaveTracks(simParams['noisyTrackFile'], fake_tracks, fake_falarms)
SaveCorners(simParams['inputDataFile'], simParams['corner_filestem'], simParams['frameCnt'], fake_volData)



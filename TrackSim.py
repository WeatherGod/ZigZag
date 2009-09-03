#!/usr/bin/env python

import random
from TrackFileUtils import *		# for writing the track data
import numpy
import copy				# for deep copying
import math

from TrackPlot import *

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
	    'pos': [random.uniform(min(xLims), max(xLims)),
		    random.uniform(min(yLims), max(yLims))],
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


def CreateVolData(tracks, tLims, xLims, yLims) :
    volData = []
    allCells = {'frameNums': [], 'trackID': [], 'xLocs': [], 'yLocs': []}
    for (trackID, aTrack) in enumerate(tracks) :
        allCells['frameNums'].extend(aTrack['frameNums'])
	allCells['trackID'].extend([trackID] * len(aTrack['frameNums']))
	allCells['xLocs'].extend(aTrack['xLocs'])
	allCells['yLocs'].extend(aTrack['yLocs'])
    
    
    for volTime in range(min(tLims), max(tLims) + 1) :
        volData.append({'volTime': volTime,
                        'stormCells': [{'xLoc': xLoc, 'yLoc': yLoc, 'trackID': trackID}
                                       for (xLoc, yLoc, frameNum, trackID) in zip(allCells['xLocs'], allCells['yLocs'], allCells['frameNums'], allCells['trackID'])
					if (frameNum == volTime and xLoc >= min(xLims) and xLoc <= max(xLims) and
								    yLoc >= min(yLims) and yLoc <= max(yLims))]})

    return(volData)

def DisturbTracks(true_tracks, true_volData, noise_params) :
    
    tracks = copy.deepcopy(true_tracks)
    volData = copy.deepcopy(true_volData)

    for (volIndex, aVol) in enumerate(volData) :
        xLocs = numpy.array([stormCell['xLoc'] for stormCell in aVol['stormCells']])
	yLocs = numpy.array([stormCell['yLoc'] for stormCell in aVol['stormCells']])
        distMatrix = numpy.hypot(numpy.tile(xLocs, (len(xLocs), 1)) - numpy.rollaxis(numpy.tile(xLocs, (len(xLocs), 1)), 1),
                                 numpy.tile(yLocs, (len(xLocs), 1)) - numpy.rollaxis(numpy.tile(yLocs, (len(xLocs), 1)), 1))

        
	for index1 in range(len(aVol['stormCells'])) :
	    for index2 in range(index1 + 1, len(aVol['stormCells'])) :
		if (distMatrix[index1, index2] <= noise_params['false_merge_dist'] and
		          random.uniform(0, 1) * (distMatrix[index1, index2] / noise_params['false_merge_dist']) <= noise_params['false_merge_prob']) :
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
    for (trackID, aTrack) in enumerate(tracks) :
        tracks[trackID]['frameNums'] = [frameNum for frameNum in aTrack['frameNums'] if frameNum is not None]
        tracks[trackID]['xLocs'] = [xLoc for xLoc in aTrack['xLocs'] if xLoc is not None]
        tracks[trackID]['yLocs'] = [yLoc for yLoc in aTrack['yLocs'] if yLoc is not None]

    return(tracks, volData)
		    



corner_filestem = "corners"
inputDataFile = "InDataFile"
simTrackFile = "true_tracks"

frameCnt = 9
totalTracks = 30
speed_variance = 1.5
mean_dir = 50.0
angle_variance = 30.0
endTrackProb = 0.1

tLims = [1, frameCnt]
xLims = [0, 255]
yLims = [0, 255]
speedLims = [5, 25]

#theSeed = 92395
theSeed = random.randint(0, 99999)
print "The Seed: ", theSeed

random.seed(theSeed)


true_tracks = TracksGenerator(totalTracks, tLims, xLims, yLims, speedLims, 
			      speed_variance, mean_dir, angle_variance, endTrackProb)
volume_data = CreateVolData(true_tracks, tLims, xLims, yLims)
(fake_tracks, fake_volData) = DisturbTracks(true_tracks, volume_data, {'false_merge_dist': 5.0, 'false_merge_prob': 0.2})

#PlotTracks(true_tracks, fake_tracks, xLims, yLims, tLims)
#pylab.show()

SaveTracks(simTrackFile, true_tracks)
SaveCorners(inputDataFile, corner_filestem, frameCnt, volume_data)



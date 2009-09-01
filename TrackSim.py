#!/usr/bin/env python

import random
from TrackFileUtils import *		# for writing the track data



def IncrementPoint(dataPoint, deltaT, pos_noise, speed_noise) :
    return({'time': dataPoint['time'] + deltaT,
            'pos': [dataPoint['pos'][0] + (dataPoint['speed'][0] * deltaT) + random.uniform(-pos_noise, pos_noise),
                    dataPoint['pos'][1] + (dataPoint['speed'][1] * deltaT) + random.uniform(-pos_noise, pos_noise)],
            'speed': [dataPoint['speed'][0] + random.uniform(-speed_noise, speed_noise),
                      dataPoint['speed'][1] + random.uniform(-speed_noise, speed_noise)]})




def TracksGenerator(trackCnt, tLims, xLims, yLims, 
		    speed_variance, prob_track_ends) :
    return([MakeTrack(tLims, [-25.0, 25.0], [-25.0, 25.0], 
		      speed_variance, prob_track_ends, 
		      xLims, yLims) for index in range(trackCnt)])


def MakePoint(tLims, xLocLims, yLocLims, xSpdLims, ySpdLims) :
    return({'time': random.randrange(min(tLims), max(tLims)),
	    'pos': [random.uniform(min(xLims), max(xLims)),
		    random.uniform(min(yLims), max(yLims))],
	    'speed': [random.uniform(min(xSpdLims), max(xSpdLims)),
		      random.uniform(min(ySpdLims), max(ySpdLims))]})


def MakeTrack(tLims, xSpdLims, ySpdLims, 
	      speed_variance, prob_track_ends, 
	      xLims, yLims) :
    aPoint = MakePoint(tLims, xLims, yLims, xSpdLims, ySpdLims)
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


def CreateVolData(true_tracks, tLims, xLims, yLims) :
    volData = []
    allCells = {'frameNums': [], 'xLocs': [], 'yLocs': []}
    for aTrack in true_tracks :
        allCells['frameNums'].extend(aTrack['frameNums'])
	allCells['xLocs'].extend(aTrack['xLocs'])
	allCells['yLocs'].extend(aTrack['yLocs'])
    
    
    for volTime in range(min(tLims), max(tLims) + 1) :
        volData.append({'volTime': volTime,
                        'stormCells': [{'xLoc': xLoc, 'yLoc': yLoc}
                                       for (xLoc, yLoc, frameNum) in zip(allCells['xLocs'], allCells['yLocs'], allCells['frameNums'])
					if (frameNum == volTime and xLoc >= min(xLims) and xLoc <= max(xLims) and
								    yLoc >= min(yLims) and yLoc <= max(yLims))]})

    return(volData)





corner_filestem = "corners"
inputDataFile = "InDataFile"
simTrackFile = "true_tracks"

frameCnt = 9
totalTracks = 25
speed_variance = 1.5
endTrackProb = 0.1

tLims = [1, frameCnt]
xLims = [0, 255]
yLims = [0, 255]

theSeed = 92395
#theSeed = random.randint(0, 99999)
print "The Seed: ", theSeed

random.seed(theSeed)


true_tracks = TracksGenerator(totalTracks, tLims, xLims, yLims, speed_variance, endTrackProb)
volume_data = CreateVolData(true_tracks, tLims, xLims, yLims)

SaveTracks(simTrackFile, true_tracks)
SaveCorners(inputDataFile, corner_filestem, frameCnt, volume_data)



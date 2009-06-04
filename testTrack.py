#!/usr/bin/env python


import scit
import random

import pylab



def IncrementPoint(dataPoint, deltaT) :
    return({'volTime': dataPoint['volTime'] + deltaT,
            'xLoc': dataPoint['xLoc'] + (dataPoint['speed_x'] * deltaT) + random.uniform(-0.15, 0.15),
	    'yLoc': dataPoint['yLoc'] + (dataPoint['speed_y'] * deltaT) + random.uniform(-0.15, 0.15),
	    'speed_x': dataPoint['speed_x'] + random.uniform(-0.15, 0.15),
	    'speed_y': dataPoint['speed_y'] + random.uniform(-0.15, 0.15)})

def MakeTrack(maxLength, avg_speed_x, avg_speed_y) :
    aTrack = [{'volTime': random.randrange(0, maxLength),
               'xLoc': random.uniform(25, 75), 'yLoc': random.uniform(25, 75),
	       'speed_x': avg_speed_x + random.uniform(-2, 2), 'speed_y': avg_speed_y + random.uniform(-2, 2)}]

    while (random.uniform(0, 1) > 0.05 and aTrack[-1]['volTime'] < (maxLength - 1)) :
        aTrack.append(IncrementPoint(aTrack[-1], 1))

    return(aTrack)

def TracksGenerator(trackCnt, maxLength) :
    avg_speed_x = random.uniform(5, 10)
    avg_speed_y = random.uniform(5, 10)

    return([MakeTrack(maxLength, avg_speed_x, avg_speed_y) for index in range(trackCnt)])


def CreateVolData(trueTracks, maxLength) :
    volData = []
    allCells = []
    for track in trueTracks :
        for cell in track :
	    allCells.append(cell)

    for index in range(maxLength) :
        volData.append({'volTime': index,
	                'stormCells': [{'xLoc': cell['xLoc'], 'yLoc': cell['yLoc']}
				       for cell in allCells if cell['volTime'] == index]})

    return(volData)

saveTrackImages = True
saveDir = './Images/'

#theSeed = random.randint(0, 99999)

#theSeed = 30355   # an example of track-stealing
#theSeed = 36379   # an example of track-stealing
#theSeed = 23502   # an example of threshold error
#theSeed = 43446   # an example of track-stealing
#theSeed = 59630   # an example of track-stealing

theSeed = 54202   # an EXCELLENT example of track-stealing, threshold errors
                   # and also the need to include characteristics in matching
#theSeed = 58274   # interesting example of track-stealing (starter)
#theSeed = 27256   # Cool example of track-stealing (starter)
#theSeed = 53213   # Neato example of complete destruction by track-stealing
#theSeed = 72576   # Safe and good example
#theSeed = 48114   # Track-stealing of dead track by new storm

print "The random seed:", theSeed

random.seed(theSeed)

strmAdap = {'distThresh': 40}
stateHist = []
strmTracks = []



trueTracks = TracksGenerator(3, 25)
volume_Data = CreateVolData(trueTracks, 25)




for index in range(len(volume_Data)) :
    scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, volume_Data[index])




print "=== True Tracks ==="
pylab.hold(True)
for track in trueTracks :
    print "[%d : %d]" % (track[0]['volTime'], track[-1]['volTime']), ["(%5.1f, %5.1f)" % (cell['xLoc'], cell['yLoc']) 
    								      for cell in track]
    pylab.plot([cell['xLoc'] for cell in track],
    	       [cell['yLoc'] for cell in track], 
	       'k--.', linewidth=1.5)


print("\n=== SCIT Tracks ===")
for track in strmTracks :
    print "[%d : %d]" % (track[0]['trackTime'], track[-1]['trackTime']), ["(%5.1f, %5.1f)" % (cell['strmCell']['xLoc'], cell['strmCell']['yLoc']) for cell in track]
    pylab.plot([cell['strmCell']['xLoc'] for cell in track],
               [cell['strmCell']['yLoc'] for cell in track],
	       linewidth = 2.0)

pylab.hold(False)
pylab.show()










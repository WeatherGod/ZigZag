#!/usr/bin/env python

import random
from TrackFileUtils import *		# for writing the track data
from TrackUtils import *		# for ClipTracks(), CreateVolData(), and CleanupTracks()
import ParamUtils 			# for SaveSimulationParams(), SetupParser()
import numpy
import copy				# for deep copying
import math				# for cos(), sin(), and pi


import os				# for os.sep, os.makedirs(), os.path.exists()



def IncrementPoint(dataPoint, deltaT, pos_noise, speed_noise) :
    return({'time': dataPoint['time'] + deltaT,
            'pos': [dataPoint['pos'][0] + (dataPoint['speed'][0] * deltaT) + random.uniform(-pos_noise, pos_noise),
                    dataPoint['pos'][1] + (dataPoint['speed'][1] * deltaT) + random.uniform(-pos_noise, pos_noise)],
            'speed': [dataPoint['speed'][0] + random.uniform(-speed_noise, speed_noise),
                      dataPoint['speed'][1] + random.uniform(-speed_noise, speed_noise)]})




def TracksGenerator(trackCnt, tLims, xLims, yLims, speedLims,
		    speed_variance, meanAngle, angle_variance, prob_track_ends) :
    theTracks = [dict(MakeTrack(tLims, (meanAngle - angle_variance, meanAngle + angle_variance),
		                speedLims, speed_variance, prob_track_ends, 
		                xLims, yLims),
		      trackID = index) for index in range(trackCnt)]
    theFAlarms = []
    return(CleanupTracks(theTracks, theFAlarms))


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

        # take a storm cell, and...
	for index1 in range(len(aVol['stormCells'])) :
	    trackID1 = aVol['stormCells'][index1]['trackID']
	    # Don't bother trying to occlude falarms,
	    # because their length is only 1.
	    if trackID1 < 0 : continue
	    #print "trackID1: ", trackID1

	    # ...check against the remaining storm cells.
	    for index2 in range(index1 + 1, len(aVol['stormCells'])) :
		trackID2 = aVol['stormCells'][index2]['trackID']
		#print "  trackID2: ", trackID2

		if (distMatrix[index1, index2] <= noise_params['false_merge_dist'] and
		    len(tracks[trackID1]['frameNums']) > 3 and len(tracks[trackID2]['frameNums']) > 2 and
		    random.uniform(0., 1.) * (distMatrix[index1, index2] / noise_params['false_merge_dist']) < noise_params['false_merge_prob']) :

		    #print "\nWe have Occlusion!  trackID1: %d  trackID2:  %d   frameNum: %d\n" % (trackID1, trackID2, aVol['volTime'])
		    #print tracks[trackID1]['frameNums']
		    strmID = tracks[trackID1]['frameNums'].index(aVol['volTime'])
		    for aKey in tracks[trackID1] :
			if aKey != 'trackID' : tracks[trackID1][aKey][strmID] = None

		    aVol['stormCells'][index1] = None
		    
		    # No need to continue checking against this one...
		    break
		    

	# rebuild the stormcells list, effectively removing the storms
	# flagged as a false merger.
	volData[volIndex]['stormCells'] = [aStorm for aStorm in aVol['stormCells'] if aStorm is not None]


    # rebuild the tracks list, effectively removing the storms
    # flagged as a false merger, and eliminates zero-length tracks
    # reassigns one-length tracks as a falarm.
    (tracks, falarms) = CleanupTracks(tracks, falarms)

    return(tracks, falarms, volData)

def TrackSim(simParams, simName) :
    (true_tracks, true_falarms) = TracksGenerator(simParams['totalTracks'],
						  simParams['tLims'], simParams['xLims'], simParams['yLims'],
			          		  simParams['speedLims'], simParams['speed_variance'], simParams['mean_dir'], 
			          		  simParams['angle_variance'], simParams['endTrackProb'])
    (fake_tracks, fake_falarms) = ClipTracks(true_tracks, true_falarms, simParams['xLims'], simParams['yLims'], simParams['tLims'])
    volume_data = CreateVolData(fake_tracks, fake_falarms, simParams['tLims'], simParams['xLims'], simParams['yLims'])
    (fake_tracks, fake_falarms, fake_volData) = DisturbTracks(fake_tracks, fake_falarms, volume_data, 
							      {'false_merge_dist': simParams['false_merge_dist'], 
							       'false_merge_prob': simParams['false_merge_prob']})

    # TODO: Automatically build this file, instead!
    os.system("cp ./Parameters %s/Parameters" % simName)





    return {'true_tracks': true_tracks, 'true_falarms': true_falarms,
	    'noisy_tracks': fake_tracks, 'noisy_falarms': fake_falarms,
	    'true_volumes': volume_data, 'noisy_volumes': fake_volData}



		    
if __name__ == '__main__' :
    from optparse import OptionParser	# Command-line parsing
    parser = OptionParser()
    parser.add_option("-s", "--sim", dest="simName",
		      help="Generate Tracks for SIMNAME", 
		      metavar="SIMNAME", default="NewSim")
    ParamUtils.SetupParser(parser)

    (options, args) = parser.parse_args()

    simParams = ParamUtils.ParamsFromOptions(options)

    print "The Seed: ", simParams['theSeed']

    # Seed the PRNG
    random.seed(simParams['theSeed'])

    # Create the simulation directory.
    if (not os.path.exists(options.simName)) :
        os.makedirs(options.simName)
    


    theSimulation = TrackSim(simParams, options.simName)


    ParamUtils.SaveSimulationParams(options.simName + os.sep + "simParams.conf", simParams)
    SaveTracks(simParams['simTrackFile'], theSimulation['true_tracks'], theSimulation['true_falarms'])
    SaveTracks(simParams['noisyTrackFile'], theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
    SaveCorners(simParams['inputDataFile'], simParams['corner_filestem'], simParams['frameCnt'], theSimulation['noisy_volumes'])



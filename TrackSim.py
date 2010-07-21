#!/usr/bin/env python


import TrackUtils			# for ClipTracks(), CreateVolData(), CleanupTracks(), track_dtype
import numpy				# for Numpy
import numpy.lib.recfunctions as nprf	# for .append_fields()
import os				# for os.system(), os.sep, os.makedirs(), os.path.exists()


#############################
#   Track Making
#############################
class TrackPoint :
    """
    TrackPoint is a useful data object that helps with making simulated tracks.
    When created, it will randomly initialize itself, according to parameters, to
    give it a random starting time, position, speed and direction.

    Then, the object can be simply iterated in a for loop to update its state.
    When it 'dies', or it reached the predetermined end-of-life, the iterator
    will stop (just like looping through an array or a file).

    Each iteration will yield a tuple of (trackStatus, xPos, yPos, frameNum).
    Note that track status is currently always 'M' to indicate a good track.
    Future revisions may make this a little bit more robust and allow for
    tracks to disappear and such, thereby changing its status, maybe?

    """

    def __init__(self, cornerID, tLims, xPosLims, yPosLims, angleLims, speedLims,
                       deltaT, posNoise, speedNoise, trackDeathProb) :
        """
        Create a point that will be used to create a track.

        Parameters
        ----------
        cornerID : int
            Integer to use to begin incrementally ID-ing the points generated.

        tLims : tuple of ints
            Start and end frames  E.g., (5, 12)

        xPosLims, yPosLims : tuple of floats
            The spatial domain for track initialization
            Note that this constraint is *not* applied to
            subsequent states of the track point.  In other
            words, the track can leave/enter the domain at will.
            Ex: (0.0, 255.0)

        angleLims : tuple of floats
            The limits of the initial angle that a track may move.
            The units is in degrees and is using math coordinates.
            I.E., 0.0 degrees is East, 90.0 degrees is North.
            Ex: (30.0, 60.0) to generally head NorthEast.
            Note that, like xPosLims, this constraint is only applied
            to the initialization, and the track may head anywhere afterwards.

        speedLims : tuple of floats
            The limits of the initial speed (in magnitude) that a track
            may have. Note that, like xPosLims, this constraint is only
            applied to the initialization and the track may have any
            speed afterwards.
            Ex: (5.0, 25.0)

        deltaT : float or int
            The time increment

        posNoise : float
            The variance (+/-) of the uniform noise to apply to the position
            of the track point for each iteration of the track.

        speedNoise : float
            The variance (+/-) of the uniform noise to apply to the x/y speed
            of the track point for each iteration of the track.

        trackDeathProb : float between 0 and 1
            The probability that a track will die at some particular iteration.
            0.0 for eternal tracks, 1.0 for single points.

        """
        # These are "read-only" properties that are used in iterating
        self.deltaT = deltaT
        self.posNoise = posNoise
        self.speedNoise = speedNoise
        self.trackDeathProb = trackDeathProb
        self.lastFrame = max(tLims)

        # random state for initialization in next().
        self.initFrame = numpy.random.randint(min(tLims), max(tLims))
        self.initXPos = numpy.random.uniform(min(xPosLims), max(xPosLims))
        self.initYPos = numpy.random.uniform(min(yPosLims), max(yPosLims))
        self.initSpeed = numpy.random.uniform(min(speedLims), max(speedLims))
        self.initAngle = numpy.random.uniform(min(angleLims), max(angleLims)) * (numpy.pi / 180.0)

        # These are the internal state variables that will change
        # They are set to None for now as the first call to next() will
        # initialize the state, while subsequent calls will update the state.
        self.frameNum = None
        self.xLoc = None
        self.yLoc = None
        self.xSpeed = None
        self.ySpeed = None
        self.cornerID = cornerID


    def __iter__(self) :
        return self

    def next(self) :
        """
        Each iteration through the loop will cause the point to "move" itself according to
        a psuedo-constant velocity model.
        """
        if self.frameNum is None :
            # Then this is the first call to next(), and we shall initialize the state and return that
            # Otherwise, this is a subsequent call and therefore we need to check to see if the track
            # should be ended or if it should be updated.
            self.frameNum = self.initFrame
            self.xLoc = self.initXPos
            self.yLoc = self.initYPos
            self.xSpeed = self.initSpeed * numpy.cos(self.initAngle)
            self.ySpeed = self.initSpeed * numpy.sin(self.initAngle)

        else :
            if self.frameNum >= self.lastFrame or numpy.random.uniform(0.0, 1.0) <= self.trackDeathProb :
                raise StopIteration
        
            self.frameNum += self.deltaT
            self.xLoc += (self.xSpeed * self.deltaT) + numpy.random.uniform(-self.posNoise, self.posNoise)
            self.yLoc += (self.ySpeed * self.deltaT) + numpy.random.uniform(-self.posNoise, self.posNoise)
            self.xSpeed += numpy.random.uniform(-self.speedNoise, self.speedNoise)
            self.ySpeed += numpy.random.uniform(-self.speedNoise, self.speedNoise)
            self.cornerID += 1

        return (self.xLoc, self.yLoc, self.cornerID, self.frameNum, 'M')


def MakeTrack(cornerID, tLims, angleLims, speedLims,
              speed_variance, prob_track_ends, 
              xLims, yLims) :

    aPoint = TrackPoint(cornerID, tLims, xLims, yLims, angleLims, speedLims,
                        1, 1.5, speed_variance, prob_track_ends)

    return numpy.fromiter(aPoint, TrackUtils.track_dtype)


def MakeTracks(trackCnt, tLims, xLims, yLims, speedLims,
	       speed_variance, meanAngle, angle_variance, prob_track_ends) :
    cornerID = 0
    theTracks = [None] * trackCnt
    for index in xrange(trackCnt) :
        theTracks[index] = MakeTrack(cornerID, tLims, 
                                     (meanAngle - angle_variance,
                                      meanAngle + angle_variance),
		                     speedLims, speed_variance, prob_track_ends, 
		                     xLims, yLims)
        cornerID += len(theTracks[index])

    theFAlarms = []
    TrackUtils.CleanupTracks(theTracks, theFAlarms)

    return theTracks, theFAlarms


###################################################################################################

##########################
#   Noise Making
##########################
def DisturbTracks(trueTracks, trueFalarms, tLims, noise_params) :
    """
    Perform a variety of actions to 'disturb' tracks.
    """
    
    noiseTracks = [aTrack.copy() for aTrack in trueTracks]
    noiseFalarms = [aTrack.copy() for aTrack in trueFalarms]

    FalseMerge(noiseTracks, noiseFalarms, tLims, noise_params)


    return noiseTracks, noiseFalarms




def FalseMerge(tracks, falarms, tLims, noise_params) :
    """
    Perform random "false mergers" of the tracks in volData.
    """

    # False mergers in this algorithm is only done
    # between tracks.  False Alarms are not included.
    trackStrms = numpy.hstack([nprf.append_fields(aTrack, 'trackID',
                                                  [trackIndex] * len(aTrack),
                                                  usemask=False)
                               for trackIndex, aTrack in enumerate(tracks)])

    # Go frame by frame to see which storms could be occluded.
    for volTime in xrange(min(tLims), max(tLims) + 1) :
        strmCells = trackStrms[trackStrms['frameNums'] == volTime]
        # Calc the distances between each storm cell in this volume
        distMatrix = numpy.hypot(strmCells['xLocs'] - numpy.atleast_2d(strmCells['xLocs']).T,
                                 strmCells['yLocs'] - numpy.atleast_2d(strmCells['yLocs']).T)


        # take a storm cell, and see if there is a false merger
	for strm1Index in xrange(len(strmCells)) :
            strm1TrackID = strmCells['trackID'][strm1Index]

	    # ...check strm1 against the remaining storm cells.
            # TODO: Maybe use some sort of diag or tri function
            # to get all the possible combinations in an orderly manner?
            # However, for now, this works just fine.
	    for strm2Index in xrange(strm1Index, len(strmCells)) :
                strm2TrackID = strmCells['trackID'][strm2Index]

                # See if the two points are close enough together (false_merge_dist),
                # and see if it satisfy the random chance of being merged
		if (distMatrix[strm1Index, strm2Index] <= noise_params['false_merge_dist'] and
		    len(tracks[strm1TrackID]) > 3 and len(tracks[strm2TrackID]) > 2 and
		    (numpy.random.uniform(0., 1.) * distMatrix[strm1Index, strm2Index] / 
                         noise_params['false_merge_dist'] < noise_params['false_merge_prob'])) :

		    #print "\nWe have Occlusion!  trackID1: %d  trackID2:  %d   frameNum: %d\n" % (trackID1, trackID2, aVol['volTime'])
		    #print tracks[trackID1]['frameNums']

                    # Ok, we will have strm1 occluded by strm2, remove it from the track
                    tracks[strm1TrackID] = \
                          tracks[strm1TrackID][numpy.logical_not(tracks[strm1TrackID]['frameNums'] == \
                                                                        volData[volIndex]['volTime'])]
                    
		    # No need to continue searching strm2s against this strm1
		    break

    # rebuild the tracks list and possibly move some to falarms
    TrackUtils.CleanupTracks(tracks, falarms)

#########################################################################################################

#############################
#   Track Simulator
#############################
def TrackSim(simName, simParams) :
    true_tracks, true_falarms = MakeTracks(simParams['totalTracks'],
					   simParams['tLims'],
                                           simParams['xLims'], simParams['yLims'],
			          	   simParams['speedLims'], simParams['speed_variance'],
                                           simParams['mean_dir'], simParams['angle_variance'],
                                           simParams['endTrackProb'])

    # Clip tracks to the domain
    clippedTracks, clippedFalarms = TrackUtils.ClipTracks(true_tracks,
                                                          true_falarms,
                                                          simParams['xLims'],
                                                          simParams['yLims'],
                                                          simParams['tLims'])



    fake_tracks, fake_falarms = DisturbTracks(clippedTracks, clippedFalarms,
                                              simParams['tLims'], 
		                              {'false_merge_dist':
                                                     simParams['false_merge_dist'], 
					       'false_merge_prob':
                                                     simParams['false_merge_prob']})

    # TODO: Automatically build this file, instead!
    os.system("cp ./Parameters %s/Parameters" % simName)

    volume_data = TrackUtils.CreateVolData(clippedTracks, clippedFalarms,
                                           simParams['tLims'],
                                           simParams['xLims'],
                                           simParams['yLims'])

    fake_volData = TrackUtils.CreateVolData(fake_tracks, fake_falarms,
                                            simParams['tLims'],
                                            simParams['xLims'],
                                            simParams['yLims'])

    return {'true_tracks': true_tracks, 'true_falarms': true_falarms,
	    'noisy_tracks': fake_tracks, 'noisy_falarms': fake_falarms,
	    'true_volumes': volume_data, 'noisy_volumes': fake_volData}



		    
if __name__ == '__main__' :
    from TrackFileUtils import *		# for writing the track data
    import argparse	                        # Command-line parsing
    import ParamUtils 			        # for SaveSimulationParams(), SetupParser()
    import random				# for seeding the PRNG


    parser = argparse.ArgumentParser(description="Produce a track simulation")
    parser.add_argument("simName",
		      help="Generate Tracks for SIMNAME", 
		      metavar="SIMNAME", default="NewSim")
    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    simParams = ParamUtils.ParamsFromOptions(args)

    print "Sim Name:", args.simName
    print "The Seed:", simParams['theSeed']

    # Seed the PRNG
    random.seed(simParams['theSeed'])

    # Create the simulation directory.
    if (not os.path.exists(args.simName)) :
        os.makedirs(args.simName)
    
    theSimulation = TrackSim(args.simName, simParams)


    ParamUtils.SaveSimulationParams(args.simName + os.sep + "simParams.conf", simParams)
    SaveTracks(simParams['simTrackFile'], theSimulation['true_tracks'], theSimulation['true_falarms'])
    SaveTracks(simParams['noisyTrackFile'], theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
    SaveCorners(simParams['inputDataFile'], simParams['corner_file'], simParams['frameCnt'], theSimulation['noisy_volumes'])



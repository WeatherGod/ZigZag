#!/usr/bin/env python


import TrackUtils			# for ClipTracks(), CreateVolData(), CleanupTracks(), track_dtype
import numpy				# for Numpy
import numpy.lib.recfunctions as nprf	# for .append_fields()
import os				# for os.system(), os.sep, os.makedirs(), os.path.exists()

# TODO: Better packaging!
from TrackInit import *
from MotionModel import *



#############################
#    Track Simulators
#############################
class TrackSimulator(object) :
    def __init__(self, initModel, motionModel, trackMaker) :
        self._initModel = initModel
        self._motionModel = motionModel
        self._trackMaker = trackMaker
        
    def __call__(self, cornerID, trackCnt, *makerParams) :
        theTracks = []
        for index in xrange(trackCnt) :
            newTrack = self._trackMaker(cornerID, index, self._initModel,
                                        self._motionModel, *makerParams)
        
            cornerID += len(newTrack)
            theTracks.append(numpy.sort(newTrack, 0, order=['frameNums']))

        return theTracks, cornerID


#############################
#   Track Making
#############################
class TrackPoint(object) :
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

    def __init__(self, cornerID, trackDeathProb,
                       initModel, motionModel, maxLen = 50) :
        """
        Create a point that will be used to create a track.

        Parameters
        ----------
        cornerID : int
            Integer to use to begin incrementally ID-ing the points generated.

        trackDeathProb : float between 0 and 1
            The probability that a track will die at some particular iteration.
            0.0 for eternal tracks, 1.0 for single points.

        maxLen : int
            Maximum length of the track
        """
        # These are "read-only" properties that are used in iterating
        self.trackDeathProb = trackDeathProb
        self.cornerID = cornerID
        self._motionModel = motionModel
        self._framesRemain = maxLen

        # These are the internal state variables that will change
        # subsequent calls will update the state.
        self.frameNum, self.xLoc, self.yLoc, self.xSpeed, self.ySpeed = initModel()

        # Determine if this initial state is to be reported
        self._useInitState = initModel.useInitState
        # Used to prevent the track-maker from killing a track in the first call to next()
        self._isFirstCall = True


    def __iter__(self) :
        return self

    def next(self) :
        """
        Each iteration through the loop will cause the point to "move" itself according to
        a psuedo-constant velocity model.
        """
        if self._useInitState :
            # Then this is the first call to next() and the initial data is to be used
            self._useInitState = False
        else :
            if (not self._isFirstCall and
                (numpy.random.uniform(0.0, 1.0) <= self.trackDeathProb 
                 or self._framesRemain <= 0)) :
                raise StopIteration
        
            dt, dx, dy, dVelx, dVely = self._motionModel(self.xSpeed, self.ySpeed)
            self.frameNum += dt
            self.xLoc += dx
            self.yLoc += dy
            self.xSpeed += dVelx
            self.ySpeed += dVely
            self.cornerID += 1 if not self._isFirstCall else 0

        self._framesRemain -= 1
        self._isFirstCall = False
        return self.xLoc, self.yLoc, self.cornerID, self.frameNum, 'M'

#####################################################################################
#  Track Maker Functions
def MakeTrack(cornerID, index, initModel, motionModel, probTrackEnds, maxLen) :
    aPoint = TrackPoint(cornerID, probTrackEnds, initModel, motionModel, maxLen)
    return numpy.fromiter(aPoint, TrackUtils.track_dtype)

def MakeSplit(cornerID, index, initModel, motionModel, theTracks, probTrackEnds, maxLen) :
    # Choose a frame to initiate a split.
    # Note, I want a frame like how I want my sliced bread,
    #       no end-pieces!
    frameIndex = numpy.random.random_integers(1, len(theTracks[index]) - 2)
    initModel.setsplit(theTracks[index], theTracks[index][frameIndex]['frameNums'],
                                         theTracks[index][frameIndex]['xLocs'],
                                         theTracks[index][frameIndex]['yLocs'])
    aPoint = TrackPoint(cornerID, probTrackEnds, initModel, motionModel, maxLen)
    return numpy.fromiter(aPoint, TrackUtils.track_dtype)
###################################################################################


def MakeTracks(trackGens, splitGens, mergeGens,
               trackCnts, splitCnts, mergeCnts,
               prob_track_ends, maxTrackLen) :
    cornerID = 0
    theTracks = []
    theTrackLens = []
    
    # Loop over various track generators
    for aGen, trackCnt, splitGen, splitCnt, mergeGen, mergeCnt \
                        in zip(trackGens, trackCnts,
                               splitGens, splitCnts,
                               mergeGens, mergeCnts) :
        modelTracks = []
        modelTrackLens = []
        tracks, cornerID = aGen(cornerID, trackCnt, prob_track_ends, maxTrackLen)
        modelTracks.extend(tracks)
        modelTrackLens.extend([len(aTrack) for aTrack in tracks])        

        if splitGen is not None :
            # Now, split some of those tracks
            validTracks, = numpy.nonzero(numpy.array(modelTrackLens) >= 3)
            # Currently, we are sampling without replacement.
            #   Each track can only split at most once in its life.
            tracksToSplit = [modelTracks[validTracks[anIndex]] for anIndex in 
                              numpy.random.rand(len(validTracks)).argsort()[:splitCnt]]
            splitTracks, cornerID = splitGen(cornerID, len(tracksToSplit), tracksToSplit, 0.0, maxTrackLen)
            modelTracks.extend(splitTracks)
            modelTrackLens.extend([len(aTrack) for aTrack in splitTracks])

        if mergeGen is not None :
            # Now, merge some of those tracks
            validTracks, = numpy.nonzero(numpy.array(modelTrackLens) >= 3)
            # Currently, we are sampling without replacement.
            #   Each track can only split at most once in its life.
            #   We also need to reverse these tracks so that the mergeSim
            #   will detect a reversed direction of motion
            tracksToMerge = [modelTracks[validTracks[anIndex]][::-1] for anIndex in 
                              numpy.random.rand(len(validTracks)).argsort()[:mergeCnt]]
    
            # Create merged tracks
            # We shall go with the "Benjamin Button" approach.
            # In other words, we do the same thing we did with
            # splitting tracks, but the tracks grow in reversed time.
            mergeTracks, cornerID = mergeGen(cornerID, len(tracksToMerge), tracksToMerge, 0.0, maxTrackLen)
            modelTracks.extend(mergeTracks)
            modelTrackLens.extend([len(aTrack) for aTrack in mergeTracks])

        theTracks.extend(modelTracks)
        theTrackLens.extend(modelTrackLens)

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
    NoisifyTracks(noiseTracks, noiseFalarms, noise_params)


    return noiseTracks, noiseFalarms

def NoisifyTracks(noiseTracks, noiseFalarms, noise_params) :
    """
    Noisify the positions of the points in a track, maybe even cause some
    dropouts/dropins?
    """
    for aTrack in noiseTracks :
        aTrack['xLocs'] += noise_params['loc_variance'] * numpy.random.randn(len(aTrack))
        aTrack['yLocs'] += noise_params['loc_variance'] * numpy.random.randn(len(aTrack))


def FalseMerge(tracks, falarms, tLims, noise_params) :
    """
    Perform random "false mergers" of the tracks in volData.
    """

    # False mergers in this algorithm is only done
    # between tracks.  False Alarms are not included.
    # This hstack call is merging all the tracks together into one massive array.
    #   Plus, for each track, a trackID is appended on for each point in the track
    #   to help identify the track a point came from.
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
            #       or maybe kdtrees?
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
def TrackSim(simName, initParams, motionParams,
                      tLims, xLims, yLims,
                      speedLims, speed_variance,
                      mean_dir, angle_variance,
                      **simParams) :

    initModel = UniformInit(**initParams['TrackInit'])
    motionModel = ConstVel_Model(**motionParams['StormMotion'])
    trackSim = TrackSimulator(initModel, motionModel, MakeTrack)

    clutterModel = NormalInit(**initParams['ClutterInit'])
    clutterMotion = ConstVel_Model(**motionParams['Clutter'])
    clutterSim = TrackSimulator(clutterModel, clutterMotion, MakeTrack)
                                

    splitInit_Model = SplitInit(**initParams['SplitInit'])
    splitSim = TrackSimulator(splitInit_Model, motionModel, MakeSplit)

    mergeMotion_Model = ConstVel_Model(**initParams['mergeMotion'])
    mergeSim = TrackSimulator(splitInit_Model, mergeMotion_Model, MakeSplit)

    true_tracks, true_falarms = MakeTracks((trackSim, clutterSim),
                                           (splitSim, None),
                                           (mergeSim, None),
                                           (simParams['totalTracks'], 25),
                                           (6, 0), (6, 0),
					                       simParams['endTrackProb'],
                                           max(tLims) - min(tLims))

    # Clip tracks to the domain
    clippedTracks, clippedFalarms = TrackUtils.ClipTracks(true_tracks,
                                                          true_falarms,
                                                          xLims, yLims, tLims)




    fake_tracks, fake_falarms = DisturbTracks(clippedTracks, clippedFalarms,
                                              tLims, simParams)

    # TODO: Automatically build this file, instead!
    os.system("cp ./Parameters %s/Parameters" % simName)

    volume_data = TrackUtils.CreateVolData(clippedTracks, clippedFalarms,
                                           tLims, xLims, yLims)


    fake_volData = TrackUtils.CreateVolData(fake_tracks, fake_falarms,
                                            tLims, xLims, yLims)

    return {'true_tracks': true_tracks, 'true_falarms': true_falarms,
            'noisy_tracks': fake_tracks, 'noisy_falarms': fake_falarms,
            'true_volumes': volume_data, 'noisy_volumes': fake_volData}

		    
if __name__ == '__main__' :
    from TrackFileUtils import *		# for writing the track data
    import argparse	                    # Command-line parsing
    import ParamUtils 			        # for SaveSimulationParams(), SetupParser()


    parser = argparse.ArgumentParser(description="Produce a track simulation")
    parser.add_argument("simName",
		      help="Generate Tracks for SIMNAME", 
		      metavar="SIMNAME", default="NewSim")
    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    simParams = ParamUtils.ParamsFromOptions(args)

    # TODO: temporary...
    initParams = ParamUtils._loadModelParams("InitModels.conf", "InitModels")
    motionParams = ParamUtils._loadModelParams("MotionModels.conf", "MotionModels")

    # TODO: Just for now...
    simParams['loc_variance'] = 0.5

    print "Sim Name:", args.simName
    print "The Seed:", simParams['seed']

    # Seed the PRNG
    numpy.random.seed(simParams['seed'])

    # Create the simulation directory.
    if (not os.path.exists(args.simName)) :
        os.makedirs(args.simName)
    
    theSimulation = TrackSim(args.simName, initParams, motionParams, **simParams)


    ParamUtils.SaveSimulationParams(args.simName + os.sep + "simParams.conf", simParams)
    SaveTracks(simParams['simTrackFile'], theSimulation['true_tracks'], theSimulation['true_falarms'])
    SaveTracks(simParams['noisyTrackFile'], theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
    SaveCorners(simParams['inputDataFile'], simParams['corner_file'], simParams['frameCnt'], theSimulation['noisy_volumes'])



#!/usr/bin/env python


import TrackUtils			# for ClipTracks(), CreateVolData(), CleanupTracks(), track_dtype
import numpy				# for Numpy
import numpy.lib.recfunctions as nprf	# for .append_fields()
import os				# for os.system(), os.sep, os.makedirs(), os.path.exists()

import Sim


#############################
#    Track Simulators
#############################
sim_modelList = {}

class TrackSimulator(object) :
    def __init__(self, initModel, motionModel, trackMaker) :
        self._initModel = initModel
        self._motionModel = motionModel
        self._trackMaker = trackMaker
        
    def __call__(self, cornerID, trackCnt, simState, *makerParams) :
        theTracks = []
        for index in range(trackCnt) :
            newTrack = self._trackMaker(cornerID, self._initModel,
                                        self._motionModel, *makerParams)
        
            cornerID += len(newTrack)
            theTracks.append(numpy.sort(newTrack, 0, order=['frameNums']))

        return theTracks, cornerID

sim_modelList['Tracker'] = TrackSimulator

class SplitSimulator(TrackSimulator) :
    def __call__(self, cornerID, trackCnt, simState, *makerParams) :
        theTracks = []
        # Now, split/merge some of those tracks
        validTracks, = numpy.nonzero(numpy.array(simState['theTrackLens']) >= 3)

        # Generate a list of tracks that will have a split/merge
        # Currently, we are sampling without replacement.
        #   Each track can only split at most once in its life.
        tracksToSplit = [simState['theTracks'][validTracks[anIndex]] for anIndex in 
                          numpy.random.rand(len(validTracks)).argsort()[:trackCnt]]

        for choosenTrack in tracksToSplit :
            # Choose a frame to initiate a split.
            # Note, I want a frame like how I want my sliced bread,
            #       no end-pieces!
            frameIndex = numpy.random.random_integers(1, len(choosenTrack) - 2)
            self._initModel.setsplit(choosenTrack, choosenTrack[frameIndex]['frameNums'],
                                                   choosenTrack[frameIndex]['xLocs'],
                                                   choosenTrack[frameIndex]['yLocs'])
            newTrack = self._trackMaker(cornerID, self._initModel, self._motionModel, *makerParams)
            cornerID += len(newTrack)
            theTracks.append(numpy.sort(newTrack, 0, order=['frameNums']))

        return theTracks, cornerID

sim_modelList['Splitter'] = SplitSimulator

class MergeSimulator(TrackSimulator) :
    def __call__(self, cornerID, trackCnt, simState, *makerParams) :
        theTracks = []
        # Now, split/merge some of those tracks
        validTracks, = numpy.nonzero(numpy.array(simState['theTrackLens']) >= 3)

        # Generate a list of tracks that will have a split/merge
        # Currently, we are sampling without replacement.
        #   Each track can only split at most once in its life.
        tracksToSplit = [simState['theTracks'][validTracks[anIndex]] for anIndex in 
                          numpy.random.rand(len(validTracks)).argsort()[:trackCnt]]

        for choosenTrack in tracksToSplit :
            # Reverse the track to make it look like a merge done backwards.
            choosenTrack = choosenTrack[::-1]

            # Choose a frame to initiate a split.
            # Note, I want a frame like how I want my sliced bread,
            #       no end-pieces!
            frameIndex = numpy.random.random_integers(1, len(choosenTrack) - 2)
            self._initModel.setsplit(choosenTrack, choosenTrack[frameIndex]['frameNums'],
                                                   choosenTrack[frameIndex]['xLocs'],
                                                   choosenTrack[frameIndex]['yLocs'])
            newTrack = self._trackMaker(cornerID, self._initModel, self._motionModel, *makerParams)
            cornerID += len(newTrack)
            theTracks.append(numpy.sort(newTrack, 0, order=['frameNums']))

        return theTracks, cornerID

sim_modelList['Merger'] = MergeSimulator

#####################################################################################
#  Track Maker Functions
trackMakers = {}

def MakeTrack(cornerID, initModel, motionModel, probTrackEnds, maxLen) :
    aPoint = Sim.TrackPoint(cornerID, probTrackEnds, initModel, motionModel, maxLen)
    return numpy.fromiter(aPoint, TrackUtils.track_dtype)

trackMakers['MakeTrack'] = MakeTrack
###################################################################################






def MakeTracks(trackGens, noiseModels,
               simParams, procParams,
               prob_track_ends, maxTrackLen, tLims,
               cornerID=0, simState=None, genName='Processing') :
    theTracks = []
    theFAlarms = []

    noisesToApply = procParams.pop('noises', [])
    trackCnt = int(procParams.pop('cnt', 1))

    if simState is None :
        simState = {'theTracks': [],
                    'theFAlarms': [],
                    'theTrackLens': []}


    if genName in simParams['TrackSims'] :
        tracks, cornerID = trackGens[genName](cornerID, trackCnt, simState, prob_track_ends, maxTrackLen)
        falarms = []

    elif genName == 'Processing' :
        tracks = []
        falarms = []

    else :
        # TODO: Change this to raising an exception.
        print "ERROR: Bad generator name:", genName

    TrackUtils.CleanupTracks(tracks, falarms)

    theTracks.extend(tracks)
    theFAlarms.extend(falarms)
    
    # Loop over various track generators
    for aGen in procParams :
        currState = {'theTracks': simState['theTracks'] + tracks,
                     'theFAlarms': simState['theFAlarms'] + falarms,
                     'theTrackLens': simState['theTrackLens'] + [len(aTrack) for aTrack in tracks]}

        # Recursively perform track simulations using this loop's simulation
        #   This is typically done to restrict splits/merges on only the
        #   storm tracks and allow for clutter tracks to be made without
        #   any splitting/merging done upon them.
        # This will also allow for noise models to be applied to specific
        #   subsets of the tracks.
        subTracks, subFAlarms, cornerID = MakeTracks(trackGens, noiseModels,
                                                     simParams, procParams[aGen],
                                                     prob_track_ends, maxTrackLen, tLims,
                                                     cornerID, currState, aGen)

        theTracks.extend(subTracks)
        theFAlarms.extend(subFAlarms)

    # Noisify the generated tracks.
    for aNoise in noisesToApply :
        if isinstance(noiseModels[aNoise], Sim.Noise_Lagrangian) :
            noiseModels[aNoise](theTracks, theFAlarms)

        elif isinstance(noiseModels[aNoise], Sim.Noise_Semi) :
            noiseModels[aNoise](theTracks, theFAlarms, tLims)

        elif isinstance(noiseModels[aNoise], Sim.Noise_Eularian) :
            raise NotImplemented("Eurlarian noise models not implemented yet: %s" % aNoise)

        else :
            raise ValueError("Noise model with unknown parent type: %s" % aNoise)

        TrackUtils.CleanupTracks(theTracks, theFAlarms)

    return theTracks, theFAlarms, cornerID


###################################################################################################

def MakeModels(modParams, modelList) :
    models = {}
    for modname in modParams :
        typename = modParams[modname].pop('type')
        models[modname] = modelList[typename](**modParams[modname])

    return models

def MakeGenModels(modParams, initModels, motionModels, sim_modelList, trackMakers) :
    models = {}
    for modname in modParams :
        params = modParams[modname]
        models[modname] = sim_modelList[params['type']](initModels[params['init']],
                                         motionModels[params['motion']],
                                         trackMakers[params['trackmaker']])

    return models

#############################
#   Track Simulator
#############################
def TrackSim(simName, initParams, motionParams, tracksimParams, noiseParams,
                      tLims, xLims, yLims,
                      speedLims, speed_variance,
                      mean_dir, angle_variance,
                      **simParams) :
    initModels = MakeModels(initParams, Sim.init_modelList)
    motionModels = MakeModels(motionParams, Sim.motion_modelList)
    noiseModels = MakeModels(noiseParams, Sim.noise_modelList)

    simGens = MakeGenModels(tracksimParams['TrackSims'], initModels, motionModels, sim_modelList, trackMakers)


    true_tracks, true_falarms, cornerID = MakeTracks(simGens, noiseModels,
                                                     tracksimParams,
                                                     tracksimParams['Processing'],
					                                 simParams['endTrackProb'],
                                                     max(tLims) - min(tLims), tLims)

    # Clip tracks to the domain
    clippedTracks, clippedFAlarms = TrackUtils.ClipTracks(true_tracks,
                                                          true_falarms,
                                                          xLims, yLims, tLims)


    # TODO: Automatically build this file, instead!
    os.system("cp ./Parameters %s/Parameters" % simName)

    volume_data = TrackUtils.CreateVolData(true_tracks, true_falarms,
                                           tLims, xLims, yLims)


    noise_volData = TrackUtils.CreateVolData(clippedTracks, clippedFAlarms,
                                             tLims, xLims, yLims)

    return {'true_tracks': true_tracks, 'true_falarms': true_falarms,
            'noisy_tracks': clippedTracks, 'noisy_falarms': clippedFAlarms,
            'true_volumes': volume_data, 'noisy_volumes': noise_volData}

		    
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
    tracksimParams = ParamUtils._loadModelParams("SimModels.conf", "SimModels")
    noiseParams = ParamUtils._loadModelParams("NoiseModels.conf", "NoiseModels")

    # TODO: Just for now...
    simParams['loc_variance'] = 0.5

    print "Sim Name:", args.simName
    print "The Seed:", simParams['seed']

    # Seed the PRNG
    numpy.random.seed(simParams['seed'])

    # Create the simulation directory.
    if (not os.path.exists(args.simName)) :
        os.makedirs(args.simName)
    
    theSimulation = TrackSim(args.simName, initParams, motionParams, tracksimParams, noiseParams, **simParams)


    ParamUtils.SaveSimulationParams(args.simName + os.sep + "simParams.conf", simParams)
    SaveTracks(simParams['simTrackFile'], theSimulation['true_tracks'], theSimulation['true_falarms'])
    SaveTracks(simParams['noisyTrackFile'], theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
    SaveCorners(simParams['inputDataFile'], simParams['corner_file'], simParams['frameCnt'], theSimulation['noisy_volumes'])



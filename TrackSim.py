#!/usr/bin/env python


import TrackUtils			# for ClipTracks(), CreateVolData(), CleanupTracks(), track_dtype
import numpy				# for Numpy
import numpy.lib.recfunctions as nprf	# for .append_fields()
import os				# for os.system(), os.sep, os.makedirs(), os.path.exists()

import Sim


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
               currGen,
               trackCnt, prob_track_ends, maxTrackLen,
               tLims, cornerID=0, simState=None) :
    theTracks = []
    theFAlarms = []

    noisesToApply = procParams.pop('noises', [])
    trackCnt = int(procParams.pop('cnt', trackCnt))
    prob_track_ends = float(procParams.pop('prob_track_ends', prob_track_ends))
    maxTrackLen = int(procParams.pop('maxTrackLen', maxTrackLen))

    if simState is None :
        simState = {'theTracks': [],
                    'theFAlarms': [],
                    'theTrackLens': []}

    tracks, falarms, cornerID = currGen(cornerID, trackCnt, simState, prob_track_ends, maxTrackLen)
    TrackUtils.CleanupTracks(tracks, falarms)
    trackLens = [len(aTrack) for aTrack in tracks]



    theTracks.extend(tracks)
    theFAlarms.extend(falarms)

    currState = {'theTracks': simState['theTracks'] + tracks,
                 'theFAlarms': simState['theFAlarms'] + falarms,
                 'theTrackLens': simState['theTrackLens'] + trackLens}
    
    # Loop over various track generators
    for aGen in procParams :
        # Recursively perform track simulations using this loop's simulation
        #   This is typically done to restrict splits/merges on only the
        #   storm tracks and allow for clutter tracks to be made without
        #   any splitting/merging done upon them.
        # This will also allow for noise models to be applied to specific
        #   subsets of the tracks.
        subTracks, subFAlarms, cornerID = MakeTracks(trackGens, noiseModels,
                                                     simParams, procParams[aGen],
                                                     trackGens[aGen],
                                                     trackCnt, prob_track_ends, maxTrackLen,
                                                     tLims, cornerID, currState)

        theTracks.extend(subTracks)
        theFAlarms.extend(subFAlarms)

    # Noisify the generated tracks.
    for aNoise in noisesToApply :
        noiseModels[aNoise](theTracks, theFAlarms, tLims)
        TrackUtils.CleanupTracks(theTracks, theFAlarms)

    return theTracks, theFAlarms, cornerID


###################################################################################################

def MakeModels(modParams, modelList) :
    models = {}
    for modname in modParams :
        typename = modParams[modname].pop('type')
        models[modname] = modelList[typename](**modParams[modname])

    return models

def MakeGenModels(modParams, initModels, motionModels, gen_modelList, trackMakers) :
    models = {}
    defMotion = None #modParams.pop("motion", "UNKNOWN")
    defInit = None #modParams.pop("init", "UNKNOWN")
    defType = None #modParams.pop("type", "UNKNOWN")
    defMaker = None #modParams.pop("trackmaker", "UNKNOWN")

    for modname in modParams :
        params = modParams[modname]
        genType = gen_modelList[params.get('type', defType)]
        models[modname] = genType(initModels[params.get('init', defInit)],
                                  motionModels[params.get('motion', defMotion)],
                                  trackMakers[params.get('trackmaker', defMaker)])

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

    simGens = MakeGenModels(tracksimParams['TrackSims'], initModels, motionModels,
                            Sim.gen_modelList, trackMakers)

    rootGenerator = Sim.NullGenerator()
    trackCnt = int(tracksimParams['Processing'].pop("cnt", simParams['totalTracks']))
    endTrackProb = float(tracksimParams['Processing'].pop("prob_track_ends", simParams['endTrackProb']))
    maxTrackLen = int(tracksimParams['Processing'].pop("maxTrackLen", max(tLims) - min(tLims)))


    true_tracks, true_falarms, cornerID = MakeTracks(simGens, noiseModels,
                                                     tracksimParams,
                                                     tracksimParams['Processing'],
                                                     rootGenerator,
					                                 trackCnt, endTrackProb, maxTrackLen,
                                                     tLims)

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



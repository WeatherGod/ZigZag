#!/usr/bin/env python


if __name__ == '__main__' :
    import argparse
    import os				    # for os.sep
    import ParamUtils			# for SaveSimulationParams, SetupParser, ParamsFromOptions
    from TrackSim import TrackSim
    import Sim
    from TrackFileUtils import *
    import numpy

    parser = argparse.ArgumentParser("Run and track several storm-track simulations")
    parser.add_argument("simName", type=str,
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
    parser.add_argument("simCnt", type=int,
              help="Repeat Simulation N times.",
              metavar="N", default=1)

    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    if args.simCnt <= 0 :
        parser.error("ERROR: Invalid N value: %d" % (args.simCnt))

    globalSeed = int(args.seed)
    numpy.random.seed(globalSeed)

    # TODO: temporary...
    initParams = ParamUtils._loadModelParams("InitModels.conf", "InitModels", Sim.init_modelList)
    motionParams = ParamUtils._loadModelParams("MotionModels.conf", "MotionModels", Sim.motion_modelList)
    genParams = ParamUtils._loadModelParams("GenModels.conf", "TrackGens", Sim.gen_modelList)
    noiseParams = ParamUtils._loadModelParams("NoiseModels.conf", "NoiseModels", Sim.noise_modelList)

    tracksimParams = ParamUtils._loadSimParams("SimModels.conf", "SimModels")

    if (not os.path.exists(args.simName)) :
        os.makedirs(args.simName)

    ParamUtils.Save_MultiSim_Params("%s%sMultiSim.ini" % (args.simName, os.sep),
                                    dict(simCnt=args.simCnt,
                                         globalSeed=args.seed,
                                         simName=args.simName))

    theSimSeeds = numpy.random.random_integers(9999999, size=args.simCnt)

    for index in range(args.simCnt) :
        simName = args.simName + ("%s%.3d" % (os.sep, index))
        simParams = ParamUtils.ParamsFromOptions(args, simName = simName)

        simParams['seed'] = theSimSeeds[index]
        numpy.random.seed(simParams['seed'])

        if (not os.path.exists(simName)) :
            os.makedirs(simName)

        ParamUtils.SaveSimulationParams(simName + os.sep + 'simParams.conf', simParams)
        theSimulation = TrackSim(simName, initParams.dict(), motionParams.dict(),
                                 genParams.dict(), noiseParams.dict(),
                                 tracksimParams.dict(), **simParams)

        SaveTracks(simParams['simTrackFile'], theSimulation['true_tracks'], theSimulation['true_falarms'])
        SaveTracks(simParams['noisyTrackFile'], theSimulation['noisy_tracks'], theSimulation['noisy_falarms'])
        SaveCorners(simParams['inputDataFile'], simParams['corner_file'], theSimulation['noisy_volumes'])


#!/usr/bin/env python

import os				    # for os.sep
from TrackSim import SingleSimulation
import numpy
import ParamUtils

def MultiSimulation(multiParams, globalSimParams, initParams, motionParams,
                                 genParams, noiseParams, tracksimParams) :

    # Seed the PRNG
    numpy.random.seed(multiParams['globalSeed'])

    # Create the multi-sim directory
    if (not os.path.exists(multiParams['simName'])) :
        os.makedirs(multiParams['simName'])

    ParamUtils.Save_MultiSim_Params("%s%sMultiSim.ini" % (multiParams['simName'], os.sep),
                                    multiParams)

    # Get the seeds that will be used for each sub-simulation
    theSimSeeds = numpy.random.random_integers(9999999, size=multiParams['simCnt'])

    for index, seed in enumerate(theSimSeeds) :
        simName = multiParams['simName'] + ("%s%.3d" % (os.sep, index))

        simParams = globalSimParams.copy()
        for keyname in ('simTrackFile', 'noisyTrackFile', 'inputDataFile',
                        'corner_file', 'result_file') :
            simParams[keyname] = simParams[keyname].replace(multiParams['simName'], simName, 1)
            
        simParams['seed'] = seed

        SingleSimulation(simName, simParams, initParams.dict(), motionParams.dict(),
                                  genParams.dict(), noiseParams.dict(), tracksimParams.dict())

if __name__ == '__main__' :
    import argparse
    import Sim


    parser = argparse.ArgumentParser("Run and track several storm-track simulations")
    parser.add_argument("simName", type=str,
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
    parser.add_argument("simCnt", type=int,
              help="Repeat Simulation N times.",
              metavar="N", default=1)

    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    simParams = ParamUtils.ParamsFromOptions(args)

    if args.simCnt <= 0 :
        parser.error("ERROR: Invalid N value: %d" % (args.simCnt))

    globalSeed = int(simParams['seed'])

    # TODO: temporary...
    initParams = ParamUtils._loadModelParams("InitModels.conf", "InitModels", Sim.init_modelList)
    motionParams = ParamUtils._loadModelParams("MotionModels.conf", "MotionModels", Sim.motion_modelList)
    genParams = ParamUtils._loadModelParams("GenModels.conf", "TrackGens", Sim.gen_modelList)
    noiseParams = ParamUtils._loadModelParams("NoiseModels.conf", "NoiseModels", Sim.noise_modelList)

    tracksimParams = ParamUtils._loadSimParams("SimModels.conf", "SimModels")

    multiParams = dict(simCnt=args.simCnt,
                       globalSeed=simParams['seed'],
                       simName=args.simName)

    MultiSimulation(multiParams, simParams, initParams, motionParams,
                                 genParams, noiseParams, tracksimParams)


#!/usr/bin/env python

import os				    # for os.sep
from TrackSim import SingleSimulation, SaveSimulation
import numpy
import ParamUtils

def MultiSimulation(multiParams, simConfs, globalSimParams, path='.') :

    # Seed the PRNG
    numpy.random.seed(multiParams['globalSeed'])

    dirName = path + os.sep + multiParams['simName']

    # Create the multi-sim directory
    if (not os.path.exists(dirName)) :
        os.makedirs(dirName)

    ParamUtils.Save_MultiSim_Params("%s%sMultiSim.ini" % (dirName, os.sep),
                                    multiParams)

    # Get the seeds that will be used for each sub-simulation
    theSimSeeds = numpy.random.random_integers(9999999, size=multiParams['simCnt'])

    for index, seed in enumerate(theSimSeeds) :
        subSim = "%.3d" % index

        simParams = globalSimParams.copy()
        simParams['simName'] = subSim
        #for keyname in ('simTrackFile', 'noisyTrackFile', 'inputDataFile',
        #                'corner_file', 'result_file', 'simConfFile') :
            #simParams[keyname] = subSim + os.sep + simParams[keyname]
            #simParams[keyname] = simParams[keyname].replace(multiParams['simName'], simName, 1)
            
        simParams['seed'] = seed

        theSim = SingleSimulation(simConfs, **simParams)
        SaveSimulation(theSim, simParams, simConfs,
                       path=dirName)


if __name__ == '__main__' :
    import argparse
    import Sim


    parser = argparse.ArgumentParser(description="Run and track several storm-track simulations")
    parser.add_argument("multiSim", type=str,
                      help="Generate Tracks for MULTISIM",
                      metavar="MULTISIM", default="NewMulti")
    parser.add_argument("simCnt", type=int,
              help="Repeat Simulation N times.",
              metavar="N", default=1)
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to place MULTISIM",
                        metavar="DIRNAME", default='.')

    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    simParams = ParamUtils.ParamsFromOptions(args)

    if args.simCnt <= 0 :
        parser.error("ERROR: Invalid N value: %d" % (args.simCnt))

    globalSeed = int(simParams['seed'])

    simConfFiles = ["InitModels.conf", "MotionModels.conf",
                    "GenModels.conf", "NoiseModels.conf",
                    "SimModels.conf"]

    simConfs = ParamUtils.LoadSimulatorConf(simConfFiles)

    multiParams = dict(simCnt=args.simCnt,
                       globalSeed=simParams['seed'],
                       simName=args.multiSim)

    MultiSimulation(multiParams, simConfs, simParams, path=args.directory)


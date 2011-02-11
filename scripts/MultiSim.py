#!/usr/bin/env python

import os.path
from TrackSim import SingleSimulation, SaveSimulation
import numpy
import ZigZag.ParamUtils as ParamUtils

def MultiSimulation(multiParams, simConfs, globalSimParams, path='.') :

    # Seed the PRNG
    numpy.random.seed(multiParams['globalSeed'])

    multiDir = os.path.join(path, multiParams['simName'])

    # Create the multi-sim directory
    if (not os.path.exists(multiDir)) :
        os.makedirs(multiDir)

    ParamUtils.Save_MultiSim_Params(os.path.join(multiDir, "MultiSim.ini"),
                                    multiParams)

    # Get the seeds that will be used for each sub-simulation
    theSimSeeds = numpy.random.random_integers(9999999, size=multiParams['simCnt'])

    for index, seed in enumerate(theSimSeeds) :
        subSim = "%.3d" % index

        simParams = globalSimParams.copy()
        simParams['simName'] = subSim
        simParams['seed'] = seed

        theSim = SingleSimulation(simConfs, **simParams)
        SaveSimulation(theSim, simParams, simConfs,
                       path=multiDir)


def main(args) :
    if args.simCnt <= 0 :
        parser.error("ERROR: Invalid N value: %d" % (args.simCnt))

    simParams = ParamUtils.ParamsFromOptions(args, args.multiSim)

    simConfFiles = args.simConfFiles if args.simConfFiles is not None else \
                                        ["InitModels.conf", "MotionModels.conf",
                                         "GenModels.conf", "NoiseModels.conf",
                                         "SimModels.conf"]

    simConfs = ParamUtils.LoadSimulatorConf(simConfFiles)

    multiParams = dict(simCnt=args.simCnt,
                       globalSeed=simParams['seed'],
                       simName=args.multiSim)

    MultiSimulation(multiParams, simConfs, simParams, path=args.directory)



if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Run and track several storm-track simulations")
    AddCommandParser('MultiSim', parser)
    """
    parser.add_argument("multiSim", type=str,
                      help="Generate Tracks for MULTISIM",
                      metavar="MULTISIM", default="NewMulti")
    parser.add_argument("simCnt", type=int,
              help="Repeat Simulation N times.",
              metavar="N", default=1)
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to place MULTISIM",
                        metavar="DIRNAME", default='.')
    parser.add_argument("-c", "--conf", dest="simConfFiles",
                        nargs='+',
                        help="Configuration files for the simulation.",
                        metavar="CONFFILE", default=None)
    """
    ParamUtils.SetupParser(parser)

    args = parser.parse_args()

    main(args)


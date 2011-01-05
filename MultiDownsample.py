#!/usr/bin/env python

from DownsampleSim import DownsampleTracks
from TrackFileUtils import *
from TrackUtils import *
import ParamUtils
import os
from ListRuns import Sims_of_MultiSim

def Multi_DownsampleTracks(multiParams, skipCnt, multiSim, newMulti, path='.') :
    simNames = Sims_of_MultiSim(multiSim, path)

    multiDir = path + os.sep + multiSim
    newDir = path + os.sep + newMulti

    # TODO: Improve this to actually fully resolve these to completely prevent over-writing.
    if multiDir == newDir :
        raise ValueError("The new downsampled directory is the same as the current!")

    for simName in simNames :
        dirName = multiDir + os.sep + simName
        simParams = ParamUtils.ReadSimulationParams(dirName + os.sep + 'simParams.conf')
        origTrackData = FilterMHTTracks(*ReadTracks(dirName + os.sep + simParams['simTrackFile']))
        noisyTrackData = FilterMHTTracks(*ReadTracks(dirName + os.sep + simParams['noisyTrackFile']))

        DownsampleTracks(skipCnt, simName, simName, simParams,
                         origTrackData, noisyTrackData, path=newDir)

        print "Sim:", simName

    multiParams['simName'] = newMulti
    ParamUtils.Save_MultiSim_Params(newDir + os.sep + "MultiSim.ini", multiParams)


if __name__ == '__main__' :
    import argparse         # command-line parsing


    parser = argparse.ArgumentParser(description="Copy and downsample the simulations of a scenario")
    parser.add_argument("multiSim",
              help="Downsample the simulations of MULTISIM",
              metavar="MULTISIM")
    parser.add_argument("newName",
              help="Name of the downsampled multi-sim",
              metavar="NEWMULTI")
    parser.add_argument("skipCnt", type=int,
              help="Skip CNT frames for downsampling",
              metavar="CNT")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM and NEWMULTI",
                        metavar="DIRNAME", default='.')


    args = parser.parse_args()

    multiDir = args.directory + os.sep + args.multiSim
    paramFile = multiDir + os.sep + "MultiSim.ini"
    multiParams = ParamUtils.Read_MultiSim_Params(paramFile)

    Multi_DownsampleTracks(multiParams, args.skipCnt, args.multiSim, args.newName, path=args.directory)

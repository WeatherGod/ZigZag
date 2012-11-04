#!/usr/bin/env python
from __future__ import print_function
from ZigZag.DownsampleUtils import DownsampleTracks
from ZigZag.TrackFileUtils import *
from ZigZag.TrackUtils import *
import ZigZag.ParamUtils as ParamUtils
import os.path
from ZigZag.ListRuns import Sims_of_MultiSim

from multiprocessing import Pool

def _prepare_and_down(simName, skipCnt, multiSim, multiDir, newDir) :
    try :
        dirName = os.path.join(multiDir, simName)
        simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName, 'simParams.conf'))
        volData = ReadCorners(os.path.join(dirName, simParams['inputDataFile']),
                              path=dirName)['volume_data'] 
        origTrackData = FilterMHTTracks(*ReadTracks(os.path.join(dirName,
                                                                 simParams['simTrackFile'])))
        noisyTrackData = FilterMHTTracks(*ReadTracks(os.path.join(dirName,
                                                                  simParams['noisyTrackFile'])))

        DownsampleTracks(skipCnt, simName, simName, simParams,
                         origTrackData, noisyTrackData, volData,
                         path=newDir)

        print("Sim:", simName)
    except Exception as err :
        print(err)
        raise err


def Multi_DownsampleTracks(multiParams, skipCnt, multiSim, newMulti, path='.') :
    simNames = Sims_of_MultiSim(multiSim, path)

    multiDir = os.path.join(path, multiSim)
    newDir = os.path.join(path, newMulti)

    # TODO: Improve this to actually fully resolve these to completely prevent over-writing.
    if multiDir == newDir :
        raise ValueError("The new downsampled directory is the same as the current!")

    p = Pool()

    for simName in simNames :
        p.apply_async(_prepare_and_down, (simName, skipCnt, multiSim, multiDir, newDir))

    p.close()
    p.join()

    multiParams['simName'] = newMulti
    ParamUtils.Save_MultiSim_Params(os.path.join(newDir, "MultiSim.ini"),
                                    multiParams)


def main(args) :
    multiDir = os.path.join(args.directory, args.multiSim)
    paramFile = os.path.join(multiDir, "MultiSim.ini")
    multiParams = ParamUtils.Read_MultiSim_Params(paramFile)

    Multi_DownsampleTracks(multiParams, args.skipCnt, args.multiSim, args.newName, path=args.directory)



if __name__ == '__main__' :
    import argparse         # command-line parsing
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Copy and downsample the simulations of a scenario")
    AddCommandParser('MultiDownsample', parser)
    """
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
    """

    args = parser.parse_args()

    main(args)



#!/usr/bin/env python

import os
from TrackUtils import *
from TrackFileUtils import *
import ParamUtils
import numpy as np


def DownsampleTracks(skipCnt, simName, newName, simParams, origTracks, tracks) :

    # Create the simulation directory.
    if (not os.path.exists(newName)) :
        os.makedirs(newName)
    else :
        raise ValueError("%s is an existing simulation!" % newName)

    xLims, yLims, tLims = DomainFromTracks(*tracks)

    oldTimes = np.linspace(*simParams['tLims'], num=simParams['frameCnt'], endpoint=True)
    newTimes = oldTimes[::skipCnt+1]

    newTracks = [FilterTrack(aTrack, newTimes) for aTrack in tracks[0]]
    newFAlarms = [FilterTrack(aTrack, newTimes) for aTrack in tracks[1]]

    CleanupTracks(newTracks, newFAlarms)

    xLims, yLims, tLims = DomainFromTracks(newTracks, newFAlarms)

    volData = CreateVolData(newTracks, newFAlarms,
                            tLims, xLims, yLims)

    simParams['xLims'] = xLims
    simParams['yLims'] = yLims
    simParams['tLims'] = tLims
    simParams['simName'] = newName

    
    ParamUtils.SaveSimulationParams(simParams['simName'] + os.sep + "simParams.conf", simParams)
    SaveTracks(simParams['simName'] + os.sep + simParams['simTrackFile'], *origTracks)
    SaveTracks(simParams['simName'] + os.sep + simParams['noisyTrackFile'], newTracks, newFAlarms)
    SaveCorners(simParams['simName'] + os.sep + simParams['inputDataFile'],
                simParams['simName'] + os.sep + simParams['corner_file'], volData)    



if __name__ == "__main__" :
    import argparse             # command-line parsing


    parser = argparse.ArgumentParser(description="Copy and downsample a simulation")
    parser.add_argument("simName",
              help="Downsample the tracks of SIMNAME",
              metavar="SIMNAME")
    parser.add_argument("newName",
              help="Name of the new simulation",
              metavar="SIMNAME")
    parser.add_argument("skipCnt", type=int,
              help="Skip CNT frames for downsampling",
              metavar="CNT")

    args = parser.parse_args()

    # Probably will have this be settable at the command-line
    path = '.'

    simParams = ParamUtils.ReadSimulationParams(path + os.sep + args.simName + os.sep + 'simParams.conf')
    dirName = path + os.sep + args.simName
    origTrackData = FilterMHTTracks(*ReadTracks(dirName + os.sep + simParams['simTrackFile']))
    noisyTrackData = FilterMHTTracks(*ReadTracks(dirName + os.sep + simParams['noisyTrackFile']))

    DownsampleTracks(args.skipCnt, args.simName, args.newName, simParams,
                     origTrackData, noisyTrackData)

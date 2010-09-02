#!/usr/bin/env python

import os
from TrackUtils import *
from TrackFileUtils import *
import ParamUtils


def DownsampleTracks(skipCnt, simName, newName, simParams, origTracks, tracks) :

    # Create the simulation directory.
    if (not os.path.exists(newName)) :
        os.makedirs(newName)
    else :
        raise ValueError("%s is an existing simulation!" % newName)

    xLims, yLims, tLims = DomainFromTracks(*tracks)

    newTimes = range(tLims[0], tLims[1] + 1, skipCnt + 1)

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

    simParams['corner_file'] = simParams['corner_file'].replace(simName, newName, 1)
    simParams['inputDataFile'] = simParams['inputDataFile'].replace(simName, newName, 1)
    simParams['result_file'] = simParams['result_file'].replace(simName, newName, 1)
    
    simParams['simTrackFile'] = simParams['simTrackFile'].replace(simName, newName, 1)
    simParams['noisyTrackFile'] = simParams['noisyTrackFile'].replace(simName, newName, 1)
    


    ParamUtils.SaveSimulationParams(simParams['simName'] + os.sep + "simParams.conf", simParams)
    SaveTracks(simParams['simTrackFile'], *origTracks)
    SaveTracks(simParams['noisyTrackFile'], newTracks, newFAlarms)
    SaveCorners(simParams['inputDataFile'], simParams['corner_file'], volData)    



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

    simParams = ParamUtils.ReadSimulationParams(args.simName + os.sep + 'simParams.conf')
    origTrackData = FilterMHTTracks(*ReadTracks(simParams['simTrackFile']))
    noisyTrackData = FilterMHTTracks(*ReadTracks(simParams['noisyTrackFile']))

    DownsampleTracks(args.skipCnt, args.simName, args.newName, simParams,
                     origTrackData, noisyTrackData)

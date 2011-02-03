#!/usr/bin/env python

import os
from ZigZag.TrackUtils import *
from ZigZag.TrackFileUtils import *
import ZigZag.ParamUtils as ParamUtils
import numpy as np


def DownsampleTracks(skipCnt, simName, newName, simParams, origTracks, tracks, path='.') :

    # Create the simulation directory.
    if (not os.path.exists(path + os.sep + newName)) :
        os.makedirs(path + os.sep + newName)
    else :
        raise ValueError("%s is an existing simulation!" % (path + os.sep + newName))

    # FIXME: This isn't quite right, but it might be easily fixed.
    #        Heck, it might actually already be right.
    #        The question is that do we assume that we always know
    #        what the range of frame numbers are from knowing the
    #        frameCnt, or do we always derive it from the tracks?
    #        It might be better to assume it from the frameCnt
    #        and grab it from the frameCnt...
    xLims, yLims, frameLims = DomainFromTracks(*tracks)
    newFrames = np.arange(min(frameLims), max(frameLims) + 1, skipCnt + 1)
    if simParams['frameCnt'] < 2 :
        timeStep = 0.0
    else :
        timeStep = (simParams['tLims'][1] - simParams['tLims'][0]) / float(simParams['frameCnt'] - 1)

    newTimes = simParams['tLims'][0] + timeStep * (newFrames - 1)
    tLims = (newTimes.min(), newTimes.max())
                           

    newTracks = [FilterTrack(aTrack, newFrames) for aTrack in tracks[0]]
    newFAlarms = [FilterTrack(aTrack, newFrames) for aTrack in tracks[1]]

    CleanupTracks(newTracks, newFAlarms)

    # Maybe set if a new bbox is requested?
    #xLims, yLims, tLims = DomainFromTracks(newTracks, newFAlarms)

    volData = CreateVolData(newTracks, newFAlarms,
                            newFrames, tLims, xLims, yLims)

    simParams['frameCnt'] = len(newFrames)
    # Maybe set if a new bbox is requested?
    #simParams['xLims'] = xLims
    #simParams['yLims'] = yLims
    simParams['tLims'] = tLims
    simParams['simName'] = newName

    
    #simParams['corner_file'] = simParams['corner_file'].replace(simName, newName, 1)
    #simParams['inputDataFile'] = simParams['inputDataFile'].replace(simName, newName, 1)
    #simParams['result_file'] = simParams['result_file'].replace(simName, newName, 1)
    
    #simParams['simTrackFile'] = simParams['simTrackFile'].replace(simName, newName, 1)
    #simParams['noisyTrackFile'] = simParams['noisyTrackFile'].replace(simName, newName, 1)
    

    dirName = path + os.sep + simParams['simName']
    ParamUtils.SaveSimulationParams(dirName + os.sep + "simParams.conf", simParams)
    SaveTracks(dirName + os.sep + simParams['simTrackFile'], *origTracks)
    SaveTracks(dirName + os.sep + simParams['noisyTrackFile'], newTracks, newFAlarms)
    SaveCorners(dirName + os.sep + simParams['inputDataFile'],
                simParams['corner_file'], volData, path=dirName)



if __name__ == "__main__" :
    import argparse             # command-line parsing
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Copy and downsample a simulation")
    AddCommandParser('DownsampleSim', parser)
    """
    parser.add_argument("simName",
              help="Downsample the tracks of SIMNAME",
              metavar="SIMNAME")
    parser.add_argument("newName",
              help="Name of the new simulation",
              metavar="NEWNAME")
    parser.add_argument("skipCnt", type=int,
              help="Skip CNT frames for downsampling",
              metavar="CNT")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME and NEWNAME",
                        metavar="DIRNAME", default='.')
    """
    args = parser.parse_args()

    dirName = args.directory + os.sep + args.simName
    simParams = ParamUtils.ReadSimulationParams(dirName + os.sep + 'simParams.conf')
    origTrackData = FilterMHTTracks(*ReadTracks(dirName + os.sep + simParams['simTrackFile']))
    noisyTrackData = FilterMHTTracks(*ReadTracks(dirName + os.sep + simParams['noisyTrackFile']))

    DownsampleTracks(args.skipCnt, args.simName, args.newName, simParams,
                     origTrackData, noisyTrackData, path=args.directory)


#!/usr/bin/env python

import os.path
import ZigZag.ParamUtils as ParamUtils
from ZigZag.TrackFileUtils import *
from ZigZag.TrackUtils import FilterMHTTracks
from ZigZag.DownsampleUtils import DownsampleTracks, DownsampleCorners


def main(args) :
    dirName = os.path.join(args.directory, args.simName)
    simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName, 'simParams.conf'))
    volData = ReadCorners(os.path.join(dirName, simParams['inputDataFile']),
                          path=dirName)['volume_data']

    if args.doTracks :
        origTrackData = FilterMHTTracks(*ReadTracks(os.path.join(dirName, simParams['simTrackFile'])))
        noisyTrackData = FilterMHTTracks(*ReadTracks(os.path.join(dirName, simParams['noisyTrackFile'])))

        DownsampleTracks(args.skipCnt, args.simName, args.newName, simParams, volData,
                         origTrackData, noisyTrackData, path=args.directory)
    else :
        DownsampleCorners(args.skipCnt, args.simName, args.newName, simParams,
                          volData, path=args.directory)


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

    main(args)



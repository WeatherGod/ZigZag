#!/usr/bin/env python

from TrackFileUtils import *		# for writing track files, and reading corner files

from TrackUtils import FilterMHTTracks, CleanupTracks
import scit

import os                               # for os.sep.join(), os.system()

def DoTracking(tracker, trackParams, returnResults = False) :

    theTracks = None

    if tracker == "MHT" :
        theCommand = "~/Programs/MHT/tracking/trackCorners -o %s -p %s -i %s > /dev/null" % (trackParams['result_file'] + "_MHT",
                                                                                 trackParams['ParamFile'],
                                                                                 trackParams['inputDataFile'])
        print theCommand
        os.system(theCommand)

        if returnResults : theTracks = FilterMHTTracks(*ReadTracks(trackParams['result_file'] + "_MHT"))

    elif tracker == "SCIT" :
        cornerInfo = ReadCorners(trackParams['inputDataFile'])
        strmAdap = {'distThresh': 5.0}
        stateHist = []
        strmTracks = []
        infoTracks = []

        for aVol in cornerInfo['volume_data'] :
            scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol)

        scit.EndTracks(stateHist, strmTracks)

        falarms = []
        CleanupTracks(strmTracks, falarms)

        SaveTracks(trackParams['result_file'] + "_SCIT", strmTracks, falarms)

        if returnResults : theTracks = (strmTracks, [])

    else :
        print "ERROR: Unknown tracker:", tracker

    return theTracks


if __name__ == "__main__" :
    import ParamUtils	  # for reading simParams files
    import argparse       # Command-line parsing
    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME (default: %(default)s)",
                      metavar="SIMNAME", default="NewSim")
    parser.add_argument("trackers", nargs='+',
                        help="TRACKER to use for tracking the centroids",
                        metavar="TRACKER", choices=['SCIT', 'MHT'], default='SCIT')

    #SetupSimParser(parser)
    args = parser.parse_args()

    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.simName, "simParams.conf"]))

    simParams['ParamFile'] = os.sep.join([args.simName, "Parameters"])
    
    for tracker in args.trackers :
        DoTracking(tracker, simParams)


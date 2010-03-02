#!/usr/bin/env python

from TrackFileUtils import *		# for writing track files, and reading corner files
import ParamUtils			# for reading simParams files
from TrackUtils import FilterMHTTracks
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
        strmAdap = {'distThresh': 7.5}
        stateHist = []
        strmTracks = []

        for aVol in cornerInfo['volume_data'] :
            scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, aVol)

        SaveTracks(trackParams['result_file'] + "_SCIT", strmTracks)

        if returnResults : theTracks = (strmTracks, [])

    else :
        print "ERROR: Unknown tracker:", tracker

    return theTracks


if __name__ == "__main__" :
    from optparse import OptionParser       # Command-line parsing
    parser = OptionParser()
    parser.add_option("-s", "--sim", dest="simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
    #SetupSimParser(parser)
    (options, args) = parser.parse_args()

    simParams = ParamUtils.ReadSimulationParams(os.sep.join([options.simName, "simParams.conf"]))

    simParams['ParamFile'] = os.sep.join([options.simName, "Parameters"])
    
    DoTracking("MHT", simParams)
    DoTracking("SCIT", simParams)


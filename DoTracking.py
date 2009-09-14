#!/usr/bin/env python

from TrackFileUtils import *		# for writing track files, and reading corner files
from SimUtils import *			# for reading simParams files
import scit

import os                               # for os.sep.join(), os.system()

def DoTracking(simParams, simName) :
    paramFile = os.sep.join([simName, "Parameters"])

    print "~/Programs/MHT/tracking/trackCorners -o %s -p %s -i %s" % (simParams['result_filestem'] + "_MHT",
                                                                      paramFile,
                                                                      simParams['inputDataFile'])
    os.system("~/Programs/MHT/tracking/trackCorners -o %s -p %s -i %s" % (simParams['result_filestem'] + "_MHT",
								          paramFile,
								          simParams['inputDataFile']))

    cornerInfo = ReadCorners(simParams['inputDataFile'])
    strmAdap = {'distThresh': 25.0}
    stateHist = []
    strmTracks = []

    for aVol in cornerInfo['volume_data'] :
        scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, aVol)

    SaveTracks(simParams['result_filestem'] + "_SCIT", strmTracks)


if __name__ == "__main__" :
    from optparse import OptionParser       # Command-line parsing
    parser = OptionParser()
    parser.add_option("-s", "--sim", dest="simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")

    (options, args) = parser.parse_args()

    simParams = ReadSimulationParams(options.simName)

    DoTracking(simParams, options.simName)


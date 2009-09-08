#!/usr/bin/env python

from TrackFileUtils import *		# for writing track files, and reading corner files
import scit

from optparse import OptionParser       # Command-line parsing
import os                               # for os.sep.join(), os.system()

parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")

(options, args) = parser.parse_args()


inputDataFile = os.sep.join([options.simName, "InDataFile"])
outputResults = os.sep.join([options.simName, "testResults"])
paramFile = os.sep.join([options.simName, "Parameters"])

print "~/Programs/MHT/tracking/trackCorners -o %s -p %s -i %s" % (outputResults + "_MHT",
                                                                      paramFile,
                                                                      inputDataFile)
os.system("~/Programs/MHT/tracking/trackCorners -o %s -p %s -i %s" % (outputResults + "_MHT",
								      paramFile,
								      inputDataFile))

cornerInfo = ReadCorners(inputDataFile)
strmAdap = {'distThresh': 25.0}
stateHist = []
strmTracks = []

for aVol in cornerInfo['volume_data'] :
    scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, aVol)

SaveTracks(outputResults + "_SCIT", strmTracks)


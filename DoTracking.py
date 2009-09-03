#!/usr/bin/env python

from TrackFileUtils import *		# for writing track files, and reading corner files
import os
import scit


inputDataFile = "InDataFile"
outputResults = "testyResults"
paramFile = "Parameters"


os.system("~/Programs/MHT/tracking/trackCorners -o %s -p %s -i %s" % (outputResults + "_MHT", paramFile, inputDataFile))

cornerInfo = ReadCorners(inputDataFile)
strmAdap = {'distThresh': 25.0}
stateHist = []
strmTracks = []

for aVol in cornerInfo['volume_data'] :
    scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, aVol)

SaveTracks(outputResults + "_SCIT", strmTracks)


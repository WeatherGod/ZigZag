#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()

import argparse 			# Command-line parsing
import os				# for os.sep.join()

parser = argparse.ArgumentParser()
parser.add_argument("simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")

args = parser.parse_args()



simTrackFile = os.sep.join([args.simName, "true_tracks"])
noiseTrackFile = os.sep.join([args.simName, "noise_tracks"])


(true_tracks, true_falarms) = ReadTracks(simTrackFile)
(noise_tracks, noise_falarms) = ReadTracks(noiseTrackFile)
(xLims, yLims, tLims) = DomainFromTracks(noise_tracks['tracks'])



theFig = pylab.figure()

curAxis = theFig.gca()
curAxis.hold(True)
PlotTrack(true_tracks['tracks'], xLims, yLims, tLims, color='r', linewidth=1.5, marker='.', markersize=6.0, axis = curAxis)
PlotTrack(noise_tracks['tracks'], xLims, yLims, tLims, color='k', linewidth=1.5, marker='.', markersize=6.0, axis = curAxis)
pylab.show()

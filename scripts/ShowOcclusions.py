#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()

import argparse 			# Command-line parsing
import os.path
import matplotlib.pyplot as pyplot

parser = argparse.ArgumentParser()
parser.add_argument("simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")

args = parser.parse_args()



simTrackFile = os.path.join(args.simName, "true_tracks")
noiseTrackFile = os.path.join(args.simName, "noise_tracks")


(true_tracks, true_falarms) = ReadTracks(simTrackFile)
(noise_tracks, noise_falarms) = ReadTracks(noiseTrackFile)
(xLims, yLims, frameLims) = DomainFromTracks(noise_tracks)



theFig = pyplot.figure()

curAxis = theFig.gca()
curAxis.hold(True)
PlotTrack(true_tracks, frameLims[0], frameLims[1], color='r', linewidth=1.5, marker='.', markersize=6.0, axis = curAxis)
PlotTrack(noise_tracks, frameLims[0], frameLims[1], color='k', linewidth=1.5, marker='.', markersize=6.0, axis = curAxis)
curAxis.set_xlim(xLims)
curAxis.set_ylim(yLims)
pyplot.show()

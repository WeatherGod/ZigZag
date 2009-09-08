#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()

from optparse import OptionParser	# Command-line parsing
import os				# for os.sep.join()

parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")

(options, args) = parser.parse_args()



simTrackFile = os.sep.join([options.simName, "true_tracks"])
noiseTrackFile = os.sep.join([options.simName, "noise_tracks"])


(true_tracks, true_falarms) = ReadTracks(simTrackFile)
(noise_tracks, noise_falarms) = ReadTracks(noiseTrackFile)
(xLims, yLims, tLims) = DomainFromTracks(noise_tracks['tracks'])



pylab.figure()

PlotTrack(true_tracks['tracks'], xLims, yLims, tLims, color='k', linewidth=1.5, marker='.', markersize=6.0)
pylab.title("True Tracks")

pylab.figure()

PlotTrack(noise_tracks['tracks'], xLims, yLims, tLims, color='k', linewidth=1.5, marker='.', markersize=6.0)
pylab.title("Noise Tracks")

pylab.show()

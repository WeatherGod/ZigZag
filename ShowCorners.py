#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ParamUtils           # for ReadSimulationParams()

import argparse                         # Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing
import matplotlib.pyplot as pyplot


parser = argparse.ArgumentParser(description="Produce an animation of the centroids")
parser.add_argument("inputDataFiles", nargs='*',
                    help="Use INDATAFILE for finding corner data files",
                    metavar="INDATAFILE")

parser.add_argument("-t", "--track", dest="trackFile",
                  help="Use TRACKFILE for track data",
                  metavar="TRACKFILE", default=None)

parser.add_argument("-d", "--dir", dest="directory",
          help="Base directory to work from when using --simName",
          metavar="DIRNAME", default=".")
parser.add_argument("-s", "--simName", dest="simName",
          help="Use data from the simulation SIMNAME",
          metavar="SIMNAME", default=None)

args = parser.parse_args()

inputDataFiles = []
titles = []

if args.simName is not None :
    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.directory + os.sep + args.simName, "simParams.conf"]))
    inputDataFiles.append(args.directory + os.sep + simParams['inputDataFile'])
    titles.append(args.simName)

inputDataFiles += args.inputDataFiles
titles += args.inputDataFiles


if len(inputDataFiles) == 0 : print "WARNING: No inputDataFiles given or found!"

cornerVolumes = [ReadCorners(inFileName, args.directory)['volume_data'] for inFileName in inputDataFiles]


# TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
theFig = pyplot.figure(figsize = (11, 5))

# A list to hold the animation objects so they don't go out of scope and get GC'ed
anims = []
# The animation timer so we can sync the animations.
theTimer = None

if args.trackFile is not None :
    (tracks, falarms) = FilterMHTTracks(*ReadTracks(args.trackFile))
    (xLims, yLims, tLims) = DomainFromTracks(tracks + falarms)
else :
    volumes = []
    for aVol in cornerVolumes :
        volumes.extend(aVol)
    (xLims, yLims, tLims) = DomainFromVolumes(volumes)


for (index, volData) in enumerate(cornerVolumes) :
    curAxis = theFig.add_subplot(1, len(inputDataFiles), index + 1)

    l = Animate_Corners(volData, tLims, axis=curAxis, figure=theFig, speed=0.1, loop_hold=0.0, event_source=theTimer)

    if theTimer is None :
        theTimer = l.event_source

    anims.append(l)

    curAxis.set_xlim(xLims)
    curAxis.set_ylim(yLims)
    curAxis.set_aspect("equal", 'datalim')
    curAxis.set_title(titles[index])
    curAxis.set_xlabel("X")
    curAxis.set_ylabel("Y")


pyplot.show()

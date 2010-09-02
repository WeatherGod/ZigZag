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
          help="Use data from the simulation SIMNAME for domain limits",
          metavar="SIMNAME", default=None)

args = parser.parse_args()

inputDataFiles = []
titles = []

if args.simName is not None :
    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.directory + os.sep + args.simName, "simParams.conf"]))
    dirName = args.directory + os.sep + os.path.dirname(args.simName + os.sep)
    inputDataFiles.append(dirName + os.sep + simParams['inputDataFile'])
    titles.append(args.simName)

inputDataFiles += args.inputDataFiles
titles += args.inputDataFiles


if len(inputDataFiles) == 0 : print "WARNING: No inputDataFiles given or found!"

cornerVolumes = [ReadCorners(inFileName, args.directory)['volume_data'] for inFileName in inputDataFiles]


# TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
theFig = pyplot.figure(figsize = (11, 5))

# A list to hold the CircleCollection arrays, it will have length 
# of max(tLims) - min(tLims) + 1
allCorners = None

if args.trackFile is not None :
    (tracks, falarms) = FilterMHTTracks(*ReadTracks(args.trackFile))
    (xLims, yLims, tLims) = DomainFromTracks(tracks + falarms)
else :
    volumes = []
    for aVol in cornerVolumes :
        volumes.extend(aVol)
    (xLims, yLims, tLims) = DomainFromVolumes(volumes)

theAnim = CornerAnimation(theFig, tLims[1] - tLims[0] + 1,
                          interval=250, blit=True)

for (index, volData) in enumerate(cornerVolumes) :
    curAxis = theFig.add_subplot(1, len(inputDataFiles), index + 1)

    corners = PlotCorners(volData, tLims, axis=curAxis)


    curAxis.set_xlim(xLims)
    curAxis.set_ylim(yLims)
    #curAxis.set_aspect("equal", 'datalim')
    curAxis.set_aspect("equal")
    curAxis.set_title(titles[index])
    curAxis.set_xlabel("X")
    curAxis.set_ylabel("Y")

    theAnim.AddCornerVolume(corners)

theAnim.save("test.mp4")

pyplot.show()

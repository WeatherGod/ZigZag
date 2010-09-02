#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ParamUtils			# for ReadSimulationParams()

import argparse				# Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing
import matplotlib.pyplot as pyplot

parser = argparse.ArgumentParser(description="Produce a display of the tracks")
parser.add_argument("trackFiles", nargs='*',
                    help="TRACKFILEs to use for display",
                    metavar="TRACKFILE", default=[])
parser.add_argument("-t", "--truth", dest="truthTrackFile",
                  help="Use TRUTHFILE for true track data",
                  metavar="TRUTHFILE", default=None)
parser.add_argument("--save", dest="saveImgFile",
		  help="Save the resulting image as FILENAME.",
		  metavar="FILENAME", default=None)
parser.add_argument("-d", "--dir", dest="directory",
		  help="Base directory to work from when using --simName",
		  metavar="DIRNAME", default=".")

parser.add_argument("--noshow", dest="doShow", action = 'store_false',
		  help="To display or not to display...",
		  default=True)
parser.add_argument("-s", "--simName", dest="simName",
		  help="Use data from the simulation SIMNAME",
		  metavar="SIMNAME", default=None)

args = parser.parse_args()


# FIXME: Currently, the code allows for trackFiles to be listed as well
#        as providing a simulation (which trackfiles are automatically grabbed).
#        Both situations can not be handled right now, though.
trackFiles = []
trackTitles = []

if args.simName is not None :
    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.directory + os.sep + args.simName, "simParams.conf"]))
    dirName = args.directory + os.sep + os.path.dirname(args.simName + os.sep)
    trackFiles = [dirName + os.sep + simParams['result_file'] + '_' + aTracker for aTracker in simParams['trackers']]
    trackTitles = simParams['trackers']

    if args.truthTrackFile is None :
        args.truthTrackFile = dirName + os.sep + simParams['noisyTrackFile']

trackFiles += args.trackFiles
trackTitles += args.trackFiles


if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"


trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in trackFiles]


# TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
theFig = pyplot.figure(figsize = (11, 5))

if args.truthTrackFile is not None :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(args.truthTrackFile))

    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

    (xLims, yLims, tLims) = DomainFromTracks(true_tracks + true_falarms)
else :
    true_AssocSegs = None
    true_FAlarmSegs = None

    stackedTracks = []
    for aTracker in trackerData :
        stackedTracks += aTracker[0] + aTracker[1]
    (xLims, yLims, tLims) = DomainFromTracks(stackedTracks)

for (index, aTracker) in enumerate(trackerData) :
    curAxis = theFig.add_subplot(1, len(trackFiles), index + 1)

    if true_AssocSegs is not None and true_FAlarmSegs is not None :
        trackAssocSegs = CreateSegments(aTracker[0])
        trackFAlarmSegs = CreateSegments(aTracker[1])
        truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs, trackAssocSegs, trackFAlarmSegs)
        PlotSegments(truthtable, tLims, axis = curAxis)
    else :
        PlotPlainTracks(aTracker[0], aTracker[1], tLims, axis=curAxis)

    curAxis.set_xlim(xLims)
    curAxis.set_ylim(yLims)
    #curAxis.set_aspect("equal", 'datalim')
    curAxis.set_aspect("equal")
    curAxis.set_title(trackTitles[index])
    curAxis.set_xlabel("X")
    curAxis.set_ylabel("Y")


if args.saveImgFile is not None :
    theFig.savefig(args.saveImgFile, dpi=300)

if args.doShow :
    pyplot.show()


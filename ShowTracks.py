#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ParamUtils			# for ReadSimulationParams()

from optparse import OptionParser	# Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing
import pylab

parser = OptionParser()
parser.add_option("-t", "--truth", dest="truthTrackFile",
                  help="Use TRUTHFILE for true track data",
                  metavar="TRUTHFILE", default=None)
parser.add_option("--save", dest="saveImgFile",
		  help="Save the resulting image as FILENAME.",
		  metavar="FILENAME", default=None)
parser.add_option("-d", "--dir", dest="directory",
		  help="Base directory to work from when using --simName",
		  metavar="DIRNAME", default=".")

parser.add_option("--noshow", dest="doShow", action = 'store_false',
		  help="To display or not to display...",
		  default=True)
parser.add_option("-s", "--simName", dest="simName",
		  help="Use data from the simulation SIMNAME",
		  metavar="SIMNAME", default=None)

(options, args) = parser.parse_args()

trackFiles = []
trackTitles = []

if options.simName is not None :
    simParams = ParamUtils.ReadSimulationParams(os.sep.join([options.directory + os.sep + options.simName, "simParams.conf"]))
    trackFiles = [options.directory + os.sep + simParams['result_file'] + '_' + aTracker for aTracker in simParams['trackers']]
    trackTitles = simParams['trackers']

    if options.truthTrackFile is None :
        options.truthTrackFile = options.directory + os.sep + simParams['noisyTrackFile']

else :
    trackFiles = args
    trackTitles = args


if len(trackFiles) == 0 : print "WARNING: No trackFiles listed!"


trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in trackFiles]

bgcolor = 'mintcream'


# TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
theFig = pylab.figure(figsize = (11, 5), facecolor=bgcolor)

if options.truthTrackFile is not None :
    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(options.truthTrackFile))

    (xLims, yLims, tLims) = DomainFromTracks(true_tracks + true_falarms)

    true_AssocSegs = CreateSegments(true_tracks)
    true_FAlarmSegs = CreateSegments(true_falarms)

    for (index, aTracker) in enumerate(trackerData) :
	trackAssocSegs = CreateSegments(aTracker[0])
	trackFAlarmSegs = CreateSegments(aTracker[1])

        truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs, trackAssocSegs, trackFAlarmSegs)

        curAxis = theFig.add_subplot(1, len(trackFiles), index + 1, axisbg = bgcolor)
        PlotSegments(truthtable, xLims, yLims, tLims, axis = curAxis)

#        curAxis.axis("equal")
        curAxis.set_title(trackTitles[index])
        curAxis.set_xlabel("X [km]")
        curAxis.set_ylabel("Y [km]")


else :
    for (index, aTracker) in enumerate(trackerData) :
        # TODO: Need to have consistent domains, maybe?
        (xLims, yLims, tLims) = DomainFromTracks(aTracker[0] + aTracker[1])

        curAxis = theFig.add_subplot(1, len(args), index + 1, axisbg = bgcolor)
        curAxis.hold(True)
        PlotTrack(aTracker[0], xLims, yLims, tLims, axis = curAxis,
		  marker = '.', markersize = 6.0, color = 'k', linewidth = 1.5)
	PlotTrack(aTracker[1], xLims, yLims, tLims, axis = curAxis,
		  marker = '.', markersize = 6.0, linestyle = ' ', color = 'r')

#        curAxis.axis("equal")
        curAxis.set_title(trackTitles[index])
        curAxis.set_xlabel("X [km]")
	curAxis.set_ylabel("Y [km]")



if options.saveImgFile is not None :
    pylab.savefig(options.saveImgFile, dpi=300, facecolor = bgcolor)

if options.doShow :
    pylab.show()

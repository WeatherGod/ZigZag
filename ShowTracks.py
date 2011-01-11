#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ParamUtils			# for ReadSimulationParams()
from ListRuns import ExpandTrackRuns




if __name__ == '__main__' :

    import argparse				# Command-line parsing
    import os				# for os.sep
    import glob				# for globbing
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

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
    parser.add_argument("-r", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to analyze.  Analyze all runs if none are given",
                        metavar="RUN", default=None)
    parser.add_argument("-l", "--layout", dest="layout", type=int,
                        nargs=2, help="Layout of the subplots (rows x columns). All plots on one row by default.",
                        metavar="NUM", default=None)

    parser.add_argument("--noshow", dest="doShow", action = 'store_false',
              help="To display or not to display...",
              default=True)
    parser.add_argument("-s", "--simName", dest="simName",
              help="Use data from the simulation SIMNAME",
              metavar="SIMNAME", default=None)

    args = parser.parse_args()

    
    # TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
    figsize = (11, 5)


    # FIXME: Currently, the code allows for trackFiles to be listed as well
    #        as providing a simulation (which trackfiles are automatically grabbed).
    #        Both situations can not be handled right now, though.
    trackFiles = []
    trackTitles = []

    if args.simName is not None :
        dirName = args.directory + os.sep + args.simName
        simParams = ParamUtils.ReadSimulationParams(dirName + os.sep + "simParams.conf")

        if args.trackRuns is not None :
            simParams['trackers'] = ExpandTrackRuns(simParams['trackers'], args.trackRuns)

        trackFiles = [dirName + os.sep + simParams['result_file'] + '_' + aTracker for aTracker in simParams['trackers']]
        trackTitles = simParams['trackers']

        if args.truthTrackFile is None :
            args.truthTrackFile = dirName + os.sep + simParams['noisyTrackFile']

    trackFiles += args.trackFiles
    trackTitles += args.trackFiles


    if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"

    if args.layout is None :
        args.layout = (1, len(trackFiles))


    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in trackFiles]


    theFig = plt.figure(figsize=figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,
                            share_all=True, axes_pad=0.32)
    
    
    if args.truthTrackFile is not None :
        (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(args.truthTrackFile))

        true_AssocSegs = CreateSegments(true_tracks)
        true_FAlarmSegs = CreateSegments(true_falarms)

        (xLims, yLims, frameLims) = DomainFromTracks(true_tracks + true_falarms)
    else :
        true_AssocSegs = None
        true_FAlarmSegs = None

        stackedTracks = []
        for aTracker in trackerData :
            stackedTracks += aTracker[0] + aTracker[1]
        (xLims, yLims, frameLims) = DomainFromTracks(stackedTracks)
    

    for (index, aTracker) in enumerate(trackerData) :
        curAxis = grid[index]

        if true_AssocSegs is not None and true_FAlarmSegs is not None :
            trackAssocSegs = CreateSegments(aTracker[0])
            trackFAlarmSegs = CreateSegments(aTracker[1])
            truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs, trackAssocSegs, trackFAlarmSegs)
            PlotSegments(truthtable, frameLims, axis=curAxis)
        else :
            PlotPlainTracks(aTracker[0], aTracker[1], frameLims, axis=curAxis)

        #curAxis.set_xlim(xLims)
        #curAxis.set_ylim(yLims)
        #curAxis.set_aspect("equal", 'datalim')
        #curAxis.set_aspect("equal")
        curAxis.set_title(trackTitles[index])
        curAxis.set_xlabel("X")
        curAxis.set_ylabel("Y")


    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile, dpi=300)

    if args.doShow :
        plt.show()


#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ZigZag.ParamUtils as ParamUtils		# for ReadSimulationParams()
from ZigZag.ListRuns import ExpandTrackRuns

def main(args) :
    import os.path
    import glob				# for globbing
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

    # FIXME: Currently, the code allows for trackFiles to be listed as well
    #        as providing a simulation (which trackfiles are automatically grabbed).
    #        Both situations can not be handled right now, though.
    trackFiles = []
    trackTitles = []

    if args.simName is not None :
        dirName = os.path.join(args.directory, args.simName)
        simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName, "simParams.conf"))

        if args.trackRuns is not None :
            simParams['trackers'] = ExpandTrackRuns(simParams['trackers'], args.trackRuns)

        trackFiles = [os.path.join(dirName, simParams['result_file'] + '_' + aTracker)
                      for aTracker in simParams['trackers']]
        if args.trackTitles is None :
            trackTitles = simParams['trackers']
        else :
            trackTitles = args.trackTitles

        if args.truthTrackFile is None :
            args.truthTrackFile = os.path.join(dirName, simParams['noisyTrackFile'])

    trackFiles += args.trackFiles

    if args.trackTitles is None :
        trackTitles += args.trackFiles
    else :
        trackTitles += args.trackTitles


    if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"

    if args.layout is None :
        args.layout = (1, len(trackFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in trackFiles]


    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout, aspect=False,
                            share_all=True, axes_pad=0.35)
    
    
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
            PlotPlainTracks(aTracker[0], aTracker[1], frameLims[0], frameLims[1], axis=curAxis)

        #curAxis.set_xlim(xLims)
        #curAxis.set_ylim(yLims)
        #curAxis.set_aspect("equal", 'datalim')
        #curAxis.set_aspect("equal")
        curAxis.set_title(trackTitles[index])
        curAxis.set_xlabel("X (km)")
        curAxis.set_ylabel("Y (km)")
         


    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile, dpi=300, bbox_inches='tight')

    if args.doShow :
        plt.show()



if __name__ == '__main__' :

    import argparse				# Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce a display of the tracks")
    AddCommandParser('ShowTracks', parser)
    """
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
    parser.add_argument("-f", "--figsize", dest="figsize", type=float,
                        nargs=2, help="Size of the figure in inches (width x height). Default: %(default)s",
                        metavar="SIZE", default=(11.0, 5.0))
    parser.add_argument("--titles", dest='trackTitles', type=str,
                        nargs='*', help="Titles to use for the figure subplots. Default is to use the filenames or the track run names.",
                        metavar="TITLE", default=None)

    parser.add_argument("--noshow", dest="doShow", action = 'store_false',
              help="To display or not to display...",
              default=True)
    parser.add_argument("-s", "--simName", dest="simName",
              help="Use data from the simulation SIMNAME",
              metavar="SIMNAME", default=None)
    """
    args = parser.parse_args()

    main(args)



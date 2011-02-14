#!/usr/bin/env python

from ZigZag.TrackPlot import PlotSegments
from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks, DomainFromTracks, CreateSegments, CompareSegments

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

def MakeComparePlots(grid, trackData, truthData, titles) :
    true_AssocSegs = None
    true_FAlarmSegs = None
    frameLims = None

    for ax, aTracker, truth, title in zip(grid, trackData, truthData, titles) :
        # Either only do this for the first pass through, or do it for all passes
        if frameLims is None or len(truthData) > 1 :
            true_AssocSegs = CreateSegments(truth[0])
            true_FAlarmSegs = CreateSegments(truth[1])

            # TODO: gotta make this get the time limits!
            xLims, yLims, frameLims = DomainFromTracks(truth[0] + truth[1])

        trackAssocSegs = CreateSegments(aTracker[0])
        trackFAlarmSegs = CreateSegments(aTracker[1])
        truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                     trackAssocSegs, trackFAlarmSegs)
        PlotSegments(truthtable, frameLims, axis=ax)

        ax.set_title(title)
        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")

def main(args) :
    if args.trackTitles is None :
        args.trackTitles = args.trackFiles

    if len(args.trackFiles) == 0 : print "WARNING: No trackFiles given!"

    if args.layout is None :
        args.layout = (1, len(args.trackFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in args.trackFiles]
    truthData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in args.truthTrackFile]

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout, aspect=False,
                            share_all=True, axes_pad=0.35)

    MakeComparePlots(grid, trackerData, truthData, args.trackTitles)

    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile, dpi=300)

    if args.doShow :
        plt.show()



if __name__ == '__main__' :

    import argparse				# Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce a display of the tracks")
    AddCommandParser('ShowCompare2', parser)
    args = parser.parse_args()

    main(args)



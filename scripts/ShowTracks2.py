#!/usr/bin/env python

from ZigZag.TrackPlot import PlotPlainTracks
from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks, DomainFromTracks
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

def MakeTrackPlots(grid, trackData, titles) :
    stackedTracks = []
    for aTracker in trackData :
        stackedTracks += aTracker[0] + aTracker[1]

    # TODO: gotta make this get the time limits!
    (xLims, yLims, frameLims) = DomainFromTracks(stackedTracks)

    for ax, aTracker, title in zip(grid, trackData, titles) :
        PlotPlainTracks(aTracker[0], aTracker[1], frameLims[0], frameLims[1], axis=ax)

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

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout, aspect=False,
                            share_all=True, axes_pad=0.35)
    
    MakeTrackPlots(grid, trackerData, args.trackTitles)

    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile, dpi=300)

    if args.doShow :
        plt.show()


if __name__ == '__main__' :

    import argparse				# Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce a display of the tracks")
    AddCommandParser('ShowTracks2', parser)
    args = parser.parse_args()

    main(args)



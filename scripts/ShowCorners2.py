#!/usr/bin/env python

from ZigZag.TrackPlot import PlotCorners, CornerAnimation
from ZigZag.TrackFileUtils import ReadCorners
from ZigZag.TrackUtils import DomainFromVolumes

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

def MakeCornerPlots(fig, grid, cornerVolumes, titles) :
    volumes = []
    frameCnts = []
    for volData in cornerVolumes :
        frameCnts.append(len(volData))
        volumes.extend(volData)

    # the info in frameLims is completely useless because we
    # can't assume that each cornerVolumes has the same frame reference.
    xLims, yLims, tLims, frameLims = DomainFromVolumes(volumes)

    theAnim = CornerAnimation(fig, max(frameCnts),
                              interval=250, blit=True)

    for ax, volData, title in zip(grid, cornerVolumes, titles) :
        corners = PlotCorners(volData, tLims, axis=ax)

        ax.set_title(title)
        ax.set_xlabel("X (km)")
        ax.set_ylabel("Y (km)")

        theAnim.AddCornerVolume(corners)

    return theAnim

def main(args) :
    import os.path

    if args.trackTitles is None :
        args.trackTitles = [os.path.dirname(filename) for filename in args.inputDataFiles]

    if len(args.inputDataFiles) == 0 : print "WARNING: No corner control files given!"

    if args.layout is None :
        args.layout = (1, len(args.inputDataFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    cornerVolumes = [ReadCorners(inFileName, os.path.dirname(inFileName))['volume_data']
                     for inFileName in args.inputDataFiles]

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,
                            share_all=True, axes_pad=0.32)

    theAnim = MakeCornerPlots(theFig, grid, cornerVolumes, args.trackTitles)

    if args.saveImgFile is not None :
        theAnim.save(args.saveImgFile)

    if args.doShow :
        plt.show()


if __name__ == '__main__' :
    import argparse                         # Command-line parsing
    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce an animation of the centroids")
    AddCommandParser('ShowCorners2', parser)
    args = parser.parse_args()

    main(args)


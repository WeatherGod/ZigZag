#!/usr/bin/env python

from ZigZag.TrackPlot import PlotCorners, CornerAnimation
from ZigZag.TrackFileUtils import ReadCorners
from ZigZag.TrackUtils import DomainFromVolumes

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

from BRadar.maputils import LatLonFrom
from mpl_toolkits.basemap import Basemap
from BRadar.maputils import PlotMapLayers, mapLayers

import numpy as np

def CoordinateTransform(centroids, cent_lon, cent_lat) :
    for cents in centroids :
        # Purposely backwards to get bearing relative to 0 North
        azi = np.rad2deg(np.arctan2(cents['xLocs'], cents['yLocs']))
        dists = np.hypot(cents['xLocs'], cents['yLocs']) * 1000
        lats, lons = LatLonFrom(cent_lat, cent_lon, dists, azi)
        cents['xLocs'] = lons
        cents['yLocs'] = lats

def MakeCornerPlots(fig, grid, cornerVolumes, titles, tail, showMap) :
    volumes = []
    frameCnts = []
    for volData in cornerVolumes :
        frameCnts.append(len(volData))
        volumes.extend(volData)

    # the info in frameLims is completely useless because we
    # can't assume that each cornerVolumes has the same frame reference.
    xLims, yLims, tLims, frameLims = DomainFromVolumes(volumes)

    if showMap :
        bmap = Basemap(projection='cyl', resolution='l',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])

    theAnim = CornerAnimation(fig, max(frameCnts),
                              tail=tail, interval=250, blit=True)

    for ax, volData, title in zip(grid, cornerVolumes, titles) :
        if showMap :
            PlotMapLayers(bmap, mapLayers, ax)
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
        else :
            ax.set_xlabel("X")
            ax.set_ylabel("Y")

        corners = PlotCorners(volData, tLims, axis=ax)

        ax.set_title(title)

        theAnim.AddCornerVolume(corners)

    return theAnim

def main(args) :
    import os.path

    if args.trackTitles is None :
        args.trackTitles = [os.path.dirname(filename) for
                            filename in args.inputDataFiles]

    if len(args.inputDataFiles) == 0 :
         print "WARNING: No corner control files given!"

    if len(args.trackTitles) != len(args.inputDataFiles) :
        raise ValueError("The number of TITLEs does not match the number"
                         " of INPUTFILEs.")

    if args.layout is None :
        args.layout = (1, len(args.inputDataFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    cornerVolumes = [ReadCorners(inFileName,
                                 os.path.dirname(inFileName))['volume_data']
                     for inFileName in args.inputDataFiles]

    if args.statLonLat is not None :
        CoordinateTransform(cornerVolumes,
                            args.statLonLat[0],
                            args.statLonLat[1])

    showMap = (args.statLonLat is not None and args.displayMap)

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,
                            share_all=True, axes_pad=0.32)

    if args.tail is None :
        args.tail = 0

    theAnim = MakeCornerPlots(theFig, grid, cornerVolumes,
                              args.trackTitles, args.tail, showMap)

    if args.saveImgFile is not None :
        theAnim.save(args.saveImgFile)

    if args.doShow :
        plt.show()


if __name__ == '__main__' :
    import argparse                         # Command-line parsing
    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce an animation of the"
                                                 " centroids")
    AddCommandParser('ShowCorners2', parser)
    args = parser.parse_args()

    main(args)


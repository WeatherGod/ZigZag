#!/usr/bin/env python

from ZigZag.TrackPlot import PlotCorners, CornerAnimation
from ZigZag.TrackFileUtils import ReadCorners
from ZigZag.TrackUtils import DomainFromVolumes

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

from BRadar.maputils import Cart2LonLat
from mpl_toolkits.basemap import Basemap
from BRadar.maputils import PlotMapLayers, mapLayers
from BRadar.radarsites import ByName

import numpy as np

def CoordinateTransform(centroids, cent_lon, cent_lat) :
    for cents in centroids :
        cents['xLocs'], cents['yLocs'] = Cart2LonLat(cent_lon, cent_lat,
                                                     cents['xLocs'],
                                                     cents['yLocs'])

def MakeCornerPlots(fig, grid, cornerVolumes, titles, showMap,
                    startFrame=None, endFrame=None, tail=None) :
    volumes = []
    frameCnts = []
    for volData in cornerVolumes :
        #frameCnts.append(len(volData))
        volumes.extend(volData)

    # the info in frameLims is completely useless because we
    # can't assume that each cornerVolumes has the same frame reference.
    xLims, yLims, tLims, frameLims = DomainFromVolumes(volumes)

    if startFrame is None :
        startFrame = frameLims[0]

    if endFrame is None :
        endFrame = frameLims[1]

    if tail is None :
        tail = endFrame - startFrame

    if showMap :
        bmap = Basemap(projection='cyl', resolution='l',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])

    theAnim = CornerAnimation(fig, endFrame - startFrame + 1,
                              tail=tail, interval=250, blit=True)

    for ax, volData, title in zip(grid, cornerVolumes, titles) :
        if showMap :
            PlotMapLayers(bmap, mapLayers, ax)
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
        else :
            ax.set_xlabel("X")
            ax.set_ylabel("Y")

        # TODO: Need to figure out a better way to handle this for
        # volume data that do not have the same number of frames
        volFrames = [frameVol['frameNum'] for frameVol in volData]
        startIdx = volFrames.index(startFrame)
        endIdx = volFrames.index(endFrame)
        volTimes = [frameVol['volTime'] for frameVol in volData]
        startT = volTimes[startIdx]
        endT = volTimes[endIdx]

        corners = PlotCorners(volData, (startT, endT), axis=ax)

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

    if args.statName is not None and args.statLonLat is None :
        statData = ByName(args.statName)[0]
        args.statLonLat = (statData['LON'], statData['LAT'])

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

    theAnim = MakeCornerPlots(theFig, grid, cornerVolumes,
                              args.trackTitles, showMap, tail=args.tail,
                              startFrame=args.startFrame,
                              endFrame=args.endFrame)

    if args.xlims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_xlim(args.xlims)

    if args.ylims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_ylim(args.ylims)

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


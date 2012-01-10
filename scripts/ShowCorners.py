#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ZigZag.ParamUtils as ZigZag          # for ReadSimulationParams()

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

def main(args) :
    import os.path			# for os.path
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid
    
    inputDataFiles = []
    titles = []

    if args.simName is not None :
        dirName = os.path.join(args.directory, args.simName)
        simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName,
                                                    "simParams.conf"))
        inputDataFiles.append(os.path.join(dirName, simParams['inputDataFile']))
        titles.append(args.simName)

    # Add on any files specified at the command-line
    inputDataFiles += args.inputDataFiles
    titles += args.inputDataFiles

    if len(inputDataFiles) == 0 :
        print "WARNING: No inputDataFiles given or found!"

    if len(titles) != len(inputDataFiles) :
        raise ValueError("The number of TITLEs does not match the"
                         " number of INPUTFILEs.")

    if args.layout is None :
        args.layout = (1, len(inputDataFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    cornerVolumes = [ReadCorners(inFileName,
                                 os.path.dirname(inFileName))['volume_data']
                     for inFileName in inputDataFiles]

    if args.statLonLat is not None :
        CoordinateTransform(cornerVolumes, args.statLonLat[0],
                                           args.statLonLat[1])

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,
                            share_all=True, axes_pad=0.32)

    # A list to hold the CircleCollection arrays, it will have length 
    # of max(tLims) - min(tLims) + 1
    allCorners = None

    if args.trackFile is not None :
        (tracks, falarms) = FilterMHTTracks(*ReadTracks(args.trackFile))

        if args.statLonLat is not None :
            CoordinateTransform(tracks + falarms,
                                args.statLonLat[0],
                                args.statLonLat[1])

        (xLims, yLims, frameLims) = DomainFromTracks(tracks + falarms)
    else :
        volumes = []
        for aVol in cornerVolumes :
            volumes.extend(aVol)
        (xLims, yLims, tLims, frameLims) = DomainFromVolumes(volumes)

    showMap = (args.statLonLat is not None and args.displayMap)

    if showMap :
        bmap = Basemap(projection='cyl', resolution='l',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])

    startFrame = args.startFrame
    endFrame = args.endFrame
    tail = args.tail

    if startFrame is None :
        startFrame = frameLims[0]

    if endFrame is None :
        endFrame = frameLims[1]

    if tail is None :
        tail = 0


    theAnim = CornerAnimation(theFig, endFrame - startFrame + 1,
                              tail=tail, interval=250, blit=False)

    for (index, volData) in enumerate(cornerVolumes) :
        curAxis = grid[index]

        if showMap :
            PlotMapLayers(bmap, mapLayers, curAxis)

        volFrames = [frameVol['frameNum'] for frameVol in volData]
        startIdx = volFrames.index(startFrame)
        endIdx = volFrames.index(endFrame)
        volTimes = [frameVol['volTime'] for frameVol in volData]
        startT = volTimes[startIdx]
        endT = volTimes[endIdx]

        corners = PlotCorners(volData, (startT, endT), axis=curAxis)

        #curAxis.set_xlim(xLims)
        #curAxis.set_ylim(yLims)
        #curAxis.set_aspect("equal", 'datalim')
        #curAxis.set_aspect("equal")
        curAxis.set_title(titles[index])
        if not showMap :
            curAxis.set_xlabel("X")
            curAxis.set_ylabel("Y")
        else :
            curAxis.set_xlabel("Longitude")
            curAxis.set_ylabel("Latitude")

        theAnim.AddCornerVolume(corners)

    if args.saveImgFile is not None :
        theAnim.save(args.saveImgFile)

    if args.doShow :
        plt.show()



if __name__ == '__main__' :
    import argparse                         # Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce an animation of"
                                                 " the centroids")
    AddCommandParser('ShowCorners', parser)
    args = parser.parse_args()

    main(args)

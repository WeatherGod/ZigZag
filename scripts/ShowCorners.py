#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackPlot import _load_verts, _to_polygons
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks(), FilterTrack()
from ZigZag.ParamUtils import ReadSimulationParams, ReadSimTagFile,\
                              process_tag_filters

from BRadar.maputils import Cart2LonLat
from mpl_toolkits.basemap import Basemap
from BRadar.maputils import PlotMapLayers, mapLayers
from BRadar.radarsites import ByName
from BRadar.plotutils import RadarAnim

import numpy as np

def CoordinateTransform(centroids, cent_lon, cent_lat) :
    for cents in centroids :
        cents['xLocs'], cents['yLocs'] = Cart2LonLat(cent_lon, cent_lat,
                                                     cents['xLocs'],
                                                     cents['yLocs'])

def CoordinateTrans_lists(frames, cent_lon, cent_lat) :
    for f in frames :
        for track in f:
            track[:, 0], track[:, 1] = Cart2LonLat(cent_lon, cent_lat,
                                                   track[:, 0], track[:, 1])



def main(args) :
    import os.path			# for os.path
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid
    
    inputDataFiles = []
    titles = []
    simTagFiles = []

    if args.simName is not None :
        dirName = os.path.join(args.directory, args.simName)
        simParams = ReadSimulationParams(os.path.join(dirName,
                                                    "simParams.conf"))
        inputDataFiles.append(os.path.join(dirName, simParams['inputDataFile']))
        titles.append(args.simName)
        simTagFiles.append(os.path.join(dirName, simParams['simTagFile']))

    # Add on any files specified at the command-line
    inputDataFiles += args.inputDataFiles
    titles += args.inputDataFiles
    if args.simTagFiles is not None :
        simTagFiles += args.simTagFiles

    if len(inputDataFiles) == 0 :
        print "WARNING: No inputDataFiles given or found!"

    if len(titles) != len(inputDataFiles) :
        raise ValueError("The number of TITLEs does not match the"
                         " number of INPUTFILEs.")

    if len(simTagFiles) < len(inputDataFiles) :
        # Not an error, just simply append None
        simTagFiles.append([None] * (len(inputDataFiles) - len(simTagFiles)))

    if args.statName is not None and args.statLonLat is None :
        statData = ByName(args.statName)[0]
        args.statLonLat = (statData['LON'], statData['LAT'])

    if args.layout is None :
        args.layout = (1, len(inputDataFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    polyfiles = args.polys

    cornerVolumes = [ReadCorners(inFileName,
                                 os.path.dirname(inFileName))['volume_data']
                     for inFileName in inputDataFiles]

    polyData = [_load_verts(f, list(vol['stormCells'] for vol in vols)) for
                f, vols in zip(polyfiles, cornerVolumes)]

    multiTags = [(ReadSimTagFile(fname) if fname is not None else None) for
                 fname in simTagFiles]

    for vols, simTags in zip(cornerVolumes, multiTags) :
        keeperIDs = process_tag_filters(simTags, args.filters)
        if keeperIDs is None :
            continue

        for vol in vols :
            vol['stormCells'] = FilterTrack(vol['stormCells'],
                                            cornerIDs=keeperIDs)

    if args.statLonLat is not None :
        for vols in cornerVolumes :
            for vol in vols :
                CoordinateTransform(vol['stormCells'],
                                    args.statLonLat[0],
                                    args.statLonLat[1])
        for verts in polyData:
            CoordinateTransform(verts,
                                args.statLonLat[0],
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

    # A common event_source for synchronizing all the animations
    theTimer = None

    # Make the corners big
    big = False

    if args.radarFile is not None and args.statLonLat is not None :
        if endFrame - frameLims[0] >= len(args.radarFile) :
            # Not enough radar files, so truncate the tracks.
            endFrame = (len(args.radarFile) + frameLims[0]) - 1
        files = args.radarFile[startFrame - frameLims[0]:(endFrame + 1) -
                                                         frameLims[0]]
        radAnim = RadarAnim(theFig, files)
        theTimer = radAnim.event_source
        for ax in grid :
            radAnim.add_axes(ax, alpha=0.6, zorder=0)

        # Radar images make it difficult to see corners, so make 'em big
        big = True
    else :
        radAnim = None

    theAnim = CornerAnimation(theFig, endFrame - startFrame + 1,
                              tail=tail, interval=250, blit=False,
                              event_source=theTimer, fade=args.fade)

    for (index, volData) in enumerate(cornerVolumes) :
        curAxis = grid[index]

        if showMap :
            PlotMapLayers(bmap, mapLayers, curAxis, zorder=0.1)

        volFrames = [frameVol['frameNum'] for frameVol in volData]
        startIdx = volFrames.index(startFrame)
        endIdx = volFrames.index(endFrame)
        volTimes = [frameVol['volTime'] for frameVol in volData]
        startT = volTimes[startIdx]
        endT = volTimes[endIdx]

        corners = PlotCorners(volData, (startT, endT), axis=curAxis,
                              big=big)

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

    polyAnims = []
    for ax, verts in zip(grid, polyData):
        from matplotlib.animation import ArtistAnimation
        polyAnim = ArtistAnimation(theFig,
                        _to_polygons(polys[startFrame:endFrame + 1], ax),
                        event_source=theTimer)
        polyAnims.append(polyAnim)

    if args.xlims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_xlim(args.xlims)

    if args.ylims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_ylim(args.ylims)

    if args.saveImgFile is not None :
        if radAnim is not None :
            radAnim = [radAnim]
        theAnim.save(args.saveImgFile, extra_anim=radAnim + polyAnims)

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

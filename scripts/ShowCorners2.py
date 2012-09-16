#!/usr/bin/env python

from ZigZag.TrackPlot import PlotCorners, CornerAnimation
from ZigZag.TrackPlot import _load_verts, _to_polygons
from ZigZag.TrackFileUtils import ReadCorners
from ZigZag.TrackUtils import DomainFromVolumes, FilterTrack
from ZigZag.ParamUtils import ReadSimTagFile, process_tag_filters

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

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

def MakeCornerPlots(fig, grid, cornerVolumes, titles,
                    showMap=False, showRadar=False,
                    startFrame=None, endFrame=None, tail=None,
                    radarFiles=None, fade=False,
                    multiTags=None, tag_filters=None) :

    if multiTags is None :
        multiTags = [None] * len(cornerVolumes)

    volumes = []
    for volData in cornerVolumes :
        volumes.extend(volData)

    # the info in frameLims is completely useless because we
    # can't assume that each cornerVolumes has the same frame reference.
    xLims, yLims, tLims, frameLims = DomainFromVolumes(volumes)

    if startFrame is None :
        startFrame = frameLims[0]

    if endFrame is None :
        endFrame = frameLims[1]

    if tail is None :
        tail = 0

    # A common event_source for synchronizing all the animations
    theTimer = None

    if showRadar :
        if endFrame - frameLims[0] >= len(radarFiles) :
            # Not enough radar files, so truncate the tracks.
            endFrame = (len(radarFiles) + frameLims[0]) - 1
        files = radarFiles[startFrame - frameLims[0]:(endFrame + 1) -
                                                     frameLims[0]]
        radAnim = RadarAnim(fig, files)
        theTimer = radAnim.event_source
        for ax in grid :
            radAnim.add_axes(ax, alpha=0.6, zorder=0)
    else :
        radAnim = None

    if showMap :
        bmap = Basemap(projection='cyl', resolution='l',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])

    theAnim = CornerAnimation(fig, endFrame - startFrame + 1,
                              tail=tail, interval=250, blit=False,
                              event_source=theTimer, fade=fade)

    for ax, volData, title, simTags in zip(grid, cornerVolumes,
                                           titles, multiTags) :
        if showMap :
            PlotMapLayers(bmap, mapLayers, ax, zorder=0.1)
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
        else :
            ax.set_xlabel("X")
            ax.set_ylabel("Y")

        keeperIDs = process_tag_filters(simTags, tag_filters)
        if keeperIDs is not None :
            for frameVol in volData :
                frameVol['stormCells'] = FilterTrack(frameVol['stormCells'],
                                                     cornerIDs=keeperIDs)

        # TODO: Need to figure out a better way to handle this for
        # volume data that do not have the same number of frames
        volFrames = [frameVol['frameNum'] for frameVol in volData]
        startIdx = volFrames.index(startFrame)
        endIdx = volFrames.index(endFrame)
        volTimes = [frameVol['volTime'] for frameVol in volData]
        startT = volTimes[startIdx]
        endT = volTimes[endIdx]

        # big=showRadar because radar maps make it difficult to see regular
        # corners.
        corners = PlotCorners(volData, (startT, endT), axis=ax, big=showRadar)

        ax.set_title(title)

        theAnim.AddCornerVolume(corners)

    return theAnim, radAnim


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

    if args.simTagFiles is None :
        args.simTagFiles = []

    polyfiles = args.polys

    cornerVolumes = [ReadCorners(inFileName,
                                 os.path.dirname(inFileName))['volume_data']
                     for inFileName in args.inputDataFiles]

    polyData = [_load_verts(f, list(vol['stormCells'] for vol in vols)) for
                f, vols in zip(polyfiles, cornerVolumes)]

    multiTags = [ReadSimTagFile(fname) for fname in args.simTagFiles]

    if len(multiTags) == 0 :
        multiTags = [None]

    if len(multiTags) < len(cornerVolumes) :
        # Rudimentary broadcasting
        tagMult = max(int(len(cornerVolumes) // len(multiTags)), 1)
        multiTags = multiTags * tagMult

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

    showMap = (args.statLonLat is not None and args.displayMap)
    showRadar = (args.statLonLat is not None and args.radarFile is not None)

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,
                            share_all=True, axes_pad=0.32)

    theAnim, radAnim = MakeCornerPlots(theFig, grid, cornerVolumes,
                                       args.trackTitles, showMap, showRadar,
                                       tail=args.tail,
                                       startFrame=args.startFrame,
                                       endFrame=args.endFrame,
                                       radarFiles=args.radarFile,
                                       fade=args.fade,
                                       multiTags=multiTags,
                                       tag_filters=args.filters)

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

    parser = argparse.ArgumentParser(description="Produce an animation of the"
                                                 " centroids")
    AddCommandParser('ShowCorners2', parser)
    args = parser.parse_args()

    main(args)


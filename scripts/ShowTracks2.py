#!/usr/bin/env python

from ZigZag.TrackPlot import PlotPlainTracks, BW_mode
from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks, DomainFromTracks, FilterTrack, \
                              CleanupTracks
from ZigZag.ParamUtils import ReadSimTagFile, process_tag_filters
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

from BRadar.maputils import Cart2LonLat
from mpl_toolkits.basemap import Basemap
from BRadar.maputils import PlotMapLayers, mapLayers
from BRadar.radarsites import ByName
from BRadar.plotutils import MakeReflectPPI
from BRadar.io import LoadRastRadar

import numpy as np

def CoordinateTransform(tracks, cent_lon, cent_lat) :
    for track in tracks :
        track['xLocs'], track['yLocs'] = Cart2LonLat(cent_lon, cent_lat,
                                                     track['xLocs'],
                                                     track['yLocs'])


def MakeTrackPlots(grid, trackData, titles, showMap,
                   endFrame=None, tail=None, fade=False,
                   multiTags=None, tag_filters=None) :
    """
    *grid*              axes_grid object
    *trackData*         a list of the lists of tracks
    *titles*            titles for each subplot
    *showMap*           boolean indicating whether to plot a map layer
    *endFrame*          Display tracks as of *frame* number. Default: last
    *tail*              How many frames to include prior to *frame* to display
                        Default: all
    *fade*              Whether or not to 'fade' old tracks
    """

    if multiTags is None :
        multiTags = [None] * len(trackData)

    stackedTracks = []
    for aTracker in trackData :
        stackedTracks += aTracker[0] + aTracker[1]

    # TODO: gotta make this get the time limits!
    (xLims, yLims, frameLims) = DomainFromTracks(stackedTracks)

    if endFrame is None :
        endFrame = frameLims[1]

    if tail is None :
        tail = endFrame - frameLims[0]

    startFrame = endFrame - tail

    if showMap :
        bmap = Basemap(projection='cyl', resolution='i',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])


    for ax, (tracks, falarms), title, simTags in zip(grid, trackData,
                                                     titles, multiTags) :
        if showMap :        
            PlotMapLayers(bmap, mapLayers, ax)
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
        else :
            ax.set_xlabel("X")
            ax.set_ylabel("Y")

        if simTags is not None :
            keeperIDs = process_tag_filters(simTags, tag_filters)

            if keeperIDs is not None :
                filtFunc = lambda trk: FilterTrack(trk, cornerIDs=keeperIDs)
                tracks = map(filtFunc, tracks)
                falarms = map(filtFunc, falarms)
                CleanupTracks(tracks, falarms)

        PlotPlainTracks(tracks, falarms,
                        startFrame, endFrame, axis=ax, fade=fade)

        ax.set_title(title)


def main(args) :
    if args.bw_mode :
        BW_mode()

    if len(args.trackFiles) == 0 : print "WARNING: No trackFiles given!"

    if args.trackTitles is None :
        args.trackTitles = args.trackFiles
    else :
        if len(args.trackTitles) != len(args.trackFiles) :
            raise ValueError("The number of TITLEs do not match the"
                             " number of TRACKFILEs.")

    if args.statName is not None and args.statLonLat is None :
        statData = ByName(args.statName)[0]
        args.statLonLat = (statData['LON'], statData['LAT'])

    if args.layout is None :
        args.layout = (1, len(args.trackFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for
                   trackFile in args.trackFiles]

    if args.statLonLat is not None :
        for aTracker in trackerData :
            CoordinateTransform(aTracker[0] + aTracker[1],
                                args.statLonLat[0],
                                args.statLonLat[1])

    if args.simTagFiles is None :
        args.simTagFiles = [None]

    multiTags = [ReadSimTagFile(fname) if fname is not None else None for
                 fname in args.simTagFiles]

    if len(trackerData) > len(multiTags) :
        # Very rudimentary broadcasting of multiTags to match trackerData
        tagMult = max(int(len(trackerData) // len(multiTags)), 1)
        multiTags = multiTags * tagMult

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout, aspect=False,
                            share_all=True, axes_pad=0.45)
    
    showMap = (args.statLonLat is not None and args.displayMap)

    # Can only do this if all other data being displayed will be in
    # lon/lat coordinates
    if args.radarFile is not None  and args.statLonLat is not None :
        if len(args.radarFile) > 1 and args.endFrame is not None :
            args.radarFile = args.radarFile[args.endFrame]
        else :
            args.radarFile = args.radarFile[-1]

        data = LoadRastRadar(args.radarFile)
        for ax in grid :
            MakeReflectPPI(data['vals'][0], data['lats'], data['lons'],
                           meth='pcmesh', ax=ax, colorbar=False,
                           axis_labels=False, zorder=0, alpha=0.6)

    MakeTrackPlots(grid, trackerData, args.trackTitles, showMap,
                   endFrame=args.endFrame, tail=args.tail, fade=args.fade,
                   multiTags=multiTags, tag_filters=args.filters)

    if args.xlims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_xlim(args.xlims)

    if args.ylims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_ylim(args.ylims)

    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile)

    if args.doShow :
        plt.show()


if __name__ == '__main__' :

    import argparse				# Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce a plain display of"
                                                 " the tracks")
    AddCommandParser('ShowTracks2', parser)
    args = parser.parse_args()

    main(args)



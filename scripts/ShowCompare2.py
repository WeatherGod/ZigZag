#!/usr/bin/env python

from ZigZag.TrackPlot import PlotSegments
from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks, DomainFromTracks, CreateSegments, CompareSegments

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

from BRadar.maputils import LatLonFrom
from mpl_toolkits.basemap import Basemap
from BRadar.maputils import PlotMapLayers, mapLayers

import numpy as np

def CoordinateTransform(tracks, cent_lon, cent_lat) :
    for track in tracks :
        # Purposely backwards to get bearing relative to 0 North
        azi = np.rad2deg(np.arctan2(track['xLocs'], track['yLocs']))
        dists = np.hypot(track['xLocs'], track['yLocs']) * 1000
        lats, lons = LatLonFrom(cent_lat, cent_lon, dists, azi)
        track['xLocs'] = lons
        track['yLocs'] = lats

def MakeComparePlots(grid, trackData, truthData, titles, showMap) :
    true_AssocSegs = None
    true_FAlarmSegs = None
    frameLims = None

    for ax, aTracker, truth, title in zip(grid, trackData, truthData, titles) :
        # Either only do this for the first pass through,
        #  or do it for all passes
        if frameLims is None or len(truthData) > 1 :
            true_AssocSegs = CreateSegments(truth[0])
            true_FAlarmSegs = CreateSegments(truth[1])

            # TODO: gotta make this get the time limits!
            xLims, yLims, frameLims = DomainFromTracks(truth[0] + truth[1])

            if showMap :
                bmap = Basemap(projection='cyl', resolution='i',
                               suppress_ticks=False,
                               llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                               urcrnrlat=yLims[1], urcrnrlon=xLims[1])
                PlotMapLayers(bmap, mapLayers, ax)

        trackAssocSegs = CreateSegments(aTracker[0])
        trackFAlarmSegs = CreateSegments(aTracker[1])
        truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                     trackAssocSegs, trackFAlarmSegs)
        PlotSegments(truthtable, frameLims, axis=ax)

        ax.set_title(title)
        if not showMap :
            ax.set_xlabel("X (km)")
            ax.set_ylabel("Y (km)")
        else :
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")

def main(args) :
    if len(args.trackFiles) == 0 :
         print "WARNING: No trackFiles given!"
    if len(args.truthTrackFile) == 0 :
         print "WARNING: No truth trackFiles given!"

    if args.trackTitles is None :
        args.trackTitles = args.trackFiles
    else :
        if len(args.trackTitles) != len(args.trackFiles) :
            raise ValueError("The number of TITLEs does not match the number"
                             " of TRACKFILEs")

    if args.layout is None :
        args.layout = (1, max(len(args.trackFiles),
                              len(args.truthTrackFile)))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for
                   trackFile in args.trackFiles]
    truthData = [FilterMHTTracks(*ReadTracks(trackFile)) for
                 trackFile in args.truthTrackFile]

    if args.statLonLat is not None :
        for aTracker in trackerData + truthData :
            CoordinateTransform(aTracker[0] + aTracker[1],
                                args.statLonLat[0],
                                args.statLonLat[1])

    if len(trackerData) != len(truthData) :
        # Basic broadcasting needed!

        if len(truthData) > len(trackerData) :
            # Need to extend track data to match with the number of truth sets
            if len(truthData) % len(trackerData) != 0 :
                raise ValueError("Can't extend TRACKFILE list to match with"
                                 " the TRUTHFILE list!")
        else :
            # Need to extend truth sets to match with the number of track data
            if len(trackerData) % len(truthData) != 0 :
                raise ValueError("Can't extend TRUTHFILE list to match with"
                                 " the TRACKFILE list!")

        trkMult = max(int(len(truthData) // len(trackerData)), 1)
        trthMult = max(int(len(trackerData) // len(truthData)), 1)

        (trackerData,
         truthData,
         args.trackTitles) = zip(trackerData * trkMult,
                                 truthData * trthMult,
                                 args.trackTitles * trkMult)

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout, aspect=False,
                            share_all=True, axes_pad=0.35)

    showMap = (args.statLonLat is not None and args.displayMap)

    MakeComparePlots(grid, trackerData, truthData, args.trackTitles, showMap)

    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile)

    if args.doShow :
        plt.show()



if __name__ == '__main__' :
    import argparse				# Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce a display of the"
                                                 " tracks compared against"
                                                 " truth data. Slightly "
                                                 " different from ShowTracks2.")
    AddCommandParser('ShowCompare2', parser)
    args = parser.parse_args()

    main(args)



#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ZigZag.ParamUtils as ParamUtils		# for ReadSimulationParams()
from ZigZag.ListRuns import ExpandTrackRuns

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

def main(args) :
    import os.path
    import glob				# for globbing
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

    # FIXME: Currently, the code allows for trackFiles to be listed as well
    #        as providing a simulation (which trackfiles are automatically
    #        grabbed). Both situations can not be handled right now, though.
    trackFiles = []
    trackTitles = []

    if args.simName is not None :
        dirName = os.path.join(args.directory, args.simName)
        simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName,
                                                    "simParams.conf"))

        if args.trackRuns is not None :
            simParams['trackers'] = ExpandTrackRuns(simParams['trackers'],
                                                    args.trackRuns)

        trackFiles = [os.path.join(dirName, simParams['result_file'] +
                                            '_' + aTracker)
                      for aTracker in simParams['trackers']]
        if args.trackTitles is None :
            trackTitles = simParams['trackers']
        else :
            trackTitles = args.trackTitles

        if args.truthTrackFile is None :
            args.truthTrackFile = os.path.join(dirName,
                                               simParams['noisyTrackFile'])

        if args.simTagFile is None :
            args.simTagFile = os.path.join(dirName, simParams['simTagFile'])

    trackFiles += args.trackFiles

    if args.trackTitles is None :
        trackTitles += args.trackFiles
    else :
        trackTitles += args.trackTitles

    if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"

    if len(trackTitles) != len(trackFiles) :
        raise ValueError("The number of TITLEs do not match the"
                         " number of TRACKFILEs.")

    if args.statName is not None and args.statLonLat is None :
        statData = ByName(args.statName)[0]
        args.statLonLat = (statData['LON'], statData['LAT'])

    if args.layout is None :
        args.layout = (1, len(trackFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for
                   trackFile in trackFiles]

    keeperIDs = None

    if args.simTagFile is not None :
        simTags = ParamUtils.ReadSimTagFile(args.simTagFile)
        keeperIDs = ParamUtils.process_tag_filters(simTags, args.filters)

    if args.statLonLat is not None :
        for aTracker in trackerData :
            CoordinateTransform(aTracker[0] + aTracker[1],
                                args.statLonLat[0],
                                args.statLonLat[1])


    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout, aspect=False,
                            share_all=True, axes_pad=0.35)


    if args.truthTrackFile is not None :
        (true_tracks,
         true_falarms) = FilterMHTTracks(*ReadTracks(args.truthTrackFile))

        if args.statLonLat is not None :
            CoordinateTransform(true_tracks + true_falarms,
                                args.statLonLat[0],
                                args.statLonLat[1])

        true_AssocSegs = CreateSegments(true_tracks)
        true_FAlarmSegs = CreateSegments(true_falarms)

        if keeperIDs is not None :
            true_AssocSegs = FilterSegments(keeperIDs, true_AssocSegs)
            true_FAlarmSegs = FilterSegments(keeperIDs, true_FAlarmSegs)


        (xLims, yLims, frameLims) = DomainFromTracks(true_tracks + true_falarms)
    else :
        true_AssocSegs = None
        true_FAlarmSegs = None

        stackedTracks = []
        for aTracker in trackerData :
            stackedTracks += aTracker[0] + aTracker[1]
        (xLims, yLims, frameLims) = DomainFromTracks(stackedTracks)

    endFrame = args.endFrame
    tail = args.tail

    if endFrame is None :
        endFrame = frameLims[1]

    if tail is None :
        tail = endFrame - frameLims[0]

    startFrame = endFrame - tail

    showMap = (args.statLonLat is not None and args.displayMap)

    if args.radarFile is not None and args.statLonLat is not None :
        if len(args.radarFile) > 1 and args.endFrame is not None :
            args.radarFile = args.radarFile[args.endFrame]
        else :
            args.radarFile = args.radarFile[-1]

        raddata = LoadRastRadar(args.radarFile)
    else :
        raddata = None

    if showMap :
        bmap = Basemap(projection='cyl', resolution='i',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])


    for index, (tracks, falarms) in enumerate(trackerData) :
        curAxis = grid[index]

        if raddata is not None :
            MakeReflectPPI(raddata['vals'][0], raddata['lats'], raddata['lons'],
                           meth='pcmesh', ax=curAxis, colorbar=False,
                           axis_labels=False, zorder=0, alpha=0.6)

        if showMap :
            PlotMapLayers(bmap, mapLayers, curAxis)

        if true_AssocSegs is not None and true_FAlarmSegs is not None :
            trackAssocSegs = CreateSegments(tracks)
            trackFAlarmSegs = CreateSegments(falarms)

            if keeperIDs is not None :
                trackAssocSegs = FilterSegments(keeperIDs, trackAssocSegs)
                trackFAlarmSegs = FilterSegments(keeperIDs, trackFAlarmSegs)

            truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                         trackAssocSegs, trackFAlarmSegs)
            PlotSegments(truthtable, (startFrame, endFrame), axis=curAxis,
                         fade=args.fade)
        else :
            if keeperIDs is not None :
                filtFunc = lambda trk: FilterTrack(trk, cornerIDs=keeperIDs)
                tracks = map(filtFunc, tracks)
                falarms = map(filtFunc, falarms)
                CleanupTracks(tracks, falarms)

            PlotPlainTracks(tracks, falarms,
                            startFrame, endFrame, axis=curAxis,
                            fade=args.fade)

        #curAxis.set_xlim(xLims)
        #curAxis.set_ylim(yLims)
        #curAxis.set_aspect("equal", 'datalim')
        #curAxis.set_aspect("equal")
        curAxis.set_title(trackTitles[index])
        if not showMap :
            curAxis.set_xlabel("X")
            curAxis.set_ylabel("Y")
        else :
            curAxis.set_xlabel("Longitude")
            curAxis.set_ylabel("Latitude")

    if args.xlims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_xlim(args.xlims)

    if args.ylims is not None and np.prod(grid.get_geometry()) > 0 :
        grid[0].set_ylim(args.ylims)

    if args.saveImgFile is not None :
        theFig.savefig(args.saveImgFile, bbox_inches='tight')

    if args.doShow :
        plt.show()



if __name__ == '__main__' :

    import argparse				# Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce a display of"
                                                 " the tracks")
    AddCommandParser('ShowTracks', parser)
    args = parser.parse_args()

    main(args)



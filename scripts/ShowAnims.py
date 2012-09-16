#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackPlot import _load_verts, _to_polygons
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks(), FilterSegments()
import ZigZag.ParamUtils as ParamUtils           # for ReadSimulationParams()
from ZigZag.ListRuns import ExpandTrackRuns

from BRadar.maputils import Cart2LonLat
from mpl_toolkits.basemap import Basemap
from BRadar.maputils import PlotMapLayers, mapLayers
from BRadar.radarsites import ByName
from BRadar.plotutils import RadarAnim

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid

#if 'animation.writer' in plt.rcParams :
#    plt.rcParams['animation.writer'] = 'ffmpeg_file'
#    plt.rcParams['animation.codec'] = 'mpeg4'
#    plt.rcParams['animation.ffmpeg_args'] = ['-f', 'mp4']


def CoordinateTransform(tracks, cent_lon, cent_lat) :
    for track in tracks :
        track['xLocs'], track['yLocs'] = Cart2LonLat(cent_lon, cent_lat,
                                                     track['xLocs'],
                                                     track['yLocs'])

def CoordinateTrans_lists(frames, cent_lon, cent_lat) :
    for f in frames :
        for track in f:
            track[:, 0], track[:, 1] = Cart2LonLat(cent_lon, cent_lat,
                                                   track[:, 0], track[:, 1])


def main(args) :
    import os.path			# for os.path.join()
    import glob				# for globbing

    if args.bw_mode :
        BW_mode()       # from TrackPlot module

    # FIXME: Currently, the code allows for trackFiles to be listed as well
    #        as providing a simulation (which trackfiles are automatically
    #        grabbed). Both situations can not be handled right now, though.
    trackFiles = []
    trackTitles = []
    polyfiles = args.polys

    if args.statName is not None and args.statLonLat is None :
        statData = ByName(args.statName)[0]
        args.statLonLat = (statData['LON'], statData['LAT'])

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
        trackTitles = simParams['trackers']

        if args.truthTrackFile is None :
            args.truthTrackFile = os.path.join(dirName,
                                               simParams['noisyTrackFile'])

        if args.simTagFile is None :
            args.simTagFile = os.path.join(dirName,
                                           simParams['simTagFile'])

    trackFiles += args.trackFiles
    trackTitles += args.trackFiles

    if args.trackTitles is not None :
        trackTitles = args.trackTitles


    if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"

    if args.layout is None :
        args.layout = (1, len(trackFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    if len(trackFiles) < len(polyfiles):
        raise ValueError("Can not have more polygon files than trackfiles!")

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for
                   trackFile in trackFiles]
    polyData = [_load_verts(f, tracks + falarms) for f, (tracks, falarms) in
                zip(polyfiles, trackerData)]

    keeperIDs = None

    if args.simTagFile is not None :
        simTags = ParamUtils.ReadSimTagFile(args.simTagFile)
        keeperIDs = ParamUtils.process_tag_filters(simTags, args.filters)

    if args.statLonLat is not None :
        for aTracker in trackerData :
            CoordinateTransform(aTracker[0] + aTracker[1],
                                args.statLonLat[0],
                                args.statLonLat[1])
        for polys in polyData:
            CoordinateTrans_lists(polys,
                                  args.statLonLat[0], args.statLonLat[1])

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,# aspect=False,
                            share_all=True, axes_pad=0.45)

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

    startFrame = args.startFrame
    endFrame = args.endFrame
    tail = args.tail

    if startFrame is None :
        startFrame = 0

    if endFrame is None :
        endFrame = frameLims[1]

    if tail is None :
        tail = endFrame - startFrame

    # A common timer for all animations for syncing purposes.
    theTimer = None

    if args.radarFile is not None and args.statLonLat is not None :
        if endFrame >= len(args.radarFile) :
            # Not enough radar files, so truncate the tracks.
            endFrame = len(args.radarFile) - 1
        files = args.radarFile[startFrame:(endFrame + 1)]
        radAnim = RadarAnim(theFig, files)
        theTimer = radAnim.event_source
        for ax in grid :
            radAnim.add_axes(ax, alpha=0.6, zorder=0)
    else :
        radAnim = None

    showMap = (args.statLonLat is not None and args.displayMap)

    if showMap :
        bmap = Basemap(projection='cyl', resolution='i',
                       suppress_ticks=False,
                       llcrnrlat=yLims[0], llcrnrlon=xLims[0],
                       urcrnrlat=yLims[1], urcrnrlon=xLims[1])


    animator = SegAnimator(theFig, startFrame, endFrame, tail,
                           event_source=theTimer, fade=args.fade)

    for index, (tracks, falarms) in enumerate(trackerData):
        curAxis = grid[index]

        if showMap :
            PlotMapLayers(bmap, mapLayers, curAxis, zorder=0.1)

        if true_AssocSegs is not None and true_FAlarmSegs is not None :
            trackAssocSegs = CreateSegments(tracks)
            trackFAlarmSegs = CreateSegments(falarms)

            if keeperIDs is not None :
                trackAssocSegs = FilterSegments(keeperIDs, trackAssocSegs)
                trackFAlarmSegs = FilterSegments(keeperIDs, trackFAlarmSegs)

            truthtable = CompareSegments(true_AssocSegs, true_FAlarmSegs,
                                         trackAssocSegs, trackFAlarmSegs)
            l, d = Animate_Segments(truthtable, (startFrame, endFrame),
                                    axis=curAxis)
        else :
            if keeperIDs is not None :
                filtFunc = lambda trk : FilterTrack(trk, cornerIDs=keeperIDs)
                tracks = map(filtFunc, tracks)
                falarms = map(filtFunc, falarms)
                CleanupTracks(tracks, falarms)

            l, d = Animate_PlainTracks(tracks, falarms,
                                       (startFrame, endFrame), axis=curAxis)

        animator._lines.extend(l)
        animator._lineData.extend(d)

        #curAxis.set_aspect("equal", 'datalim')
        #curAxis.set_aspect("equal")
        curAxis.set_title(trackTitles[index])
        if not showMap :
            curAxis.set_xlabel("X")
            curAxis.set_ylabel("Y")
        else :
            curAxis.set_xlabel("Longitude (degrees)")
            curAxis.set_ylabel("Latitude (degrees)")

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
        animator.save(args.saveImgFile, extra_anim=radAnim + polyAnims)

    if args.doShow :
        plt.show()


if __name__ == '__main__' :
    import argparse                         # Command-line parsing

    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Produce an animation of"
                                                 " the tracks")
    AddCommandParser('ShowAnims', parser)
    args = parser.parse_args()

    main(args)

    


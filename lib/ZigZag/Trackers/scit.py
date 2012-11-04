from __future__ import print_function
import numpy as np
import numpy.lib.recfunctions as nprf       # for append_fields()
from ZigZag.TrackUtils import volume_dtype, tracking_dtype, identifier_dtype



# This code serves to duplicate how SCIT does its tracking for testing purposes

# Place some startup stuff here, maybe?

def TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, volume_Data,
                   deltaT, frameOffset=0) :
    # strmHist is a vector containing info for what happened at each time-step
    # volume_Data contains the current volume's storm cells
    # strmAdap parameterizes the algorithm

    if deltaT >= strmAdap['max_timestep'] :
        # Too large a timestep... reset the tracker.
        EndTracks(stateHist, strmTracks)

    strmCnt = len(volume_Data['stormCells'])
    # The volume data has only xLocs and yLocs,
    # so we need to add some track-relevant fields
    # to the data without modifying the input data.
    currStrms = nprf.append_fields(volume_Data['stormCells'],
                                   ('st_xLocs', 'st_yLocs', 
                                    'frameNums', 'types', 'trackID'),
                                   ([np.nan] * strmCnt, [np.nan] * strmCnt,
                                    [volume_Data['frameNum']] * strmCnt,
                                    ['U'] * strmCnt,
                                    [-1] * strmCnt),
                                   dtypes=[dtype[1] for dtype in
                                           (tracking_dtype +
                                            identifier_dtype)],
                                   usemask=False)

    BestLocs(stateHist, strmTracks, infoTracks, deltaT)
    Correl_Storms(strmAdap, currStrms,
                  stateHist, strmTracks, infoTracks, deltaT)
    Compute_Speed(strmAdap, currStrms, strmTracks, infoTracks, deltaT,
                  np.array([frame['volTime'] for frame in stateHist] +
                           [volume_Data['volTime']]), frameOffset)
    (tracksToEnd,
     tracksToKeep,
     tracksToAdd) = EndTracks(stateHist, strmTracks, currStrms)


    stateHist.append({'volTime': volume_Data['volTime'],
                      'frameNum': volume_Data['frameNum'],
                      'stormCells': currStrms})

    return tracksToEnd, tracksToKeep, tracksToAdd

def EndTracks(stateHist, strmTracks, currStrms=None) :
    """
    After the storm cells have been associated with tracks, now we need to
    determine which tracks have to be 'turned off' and clean up the data in
    the track data.

    Call this function without a currStrms argument when you are finished
    tracking and want to finalize the tracks.
    """
    if currStrms is not None :
        currTracks = set(currStrms['trackID'])
    else :
        currTracks = set([])

    if len(stateHist) == 0 :
        # Ah, there is no history, therefore, there are no established tracks
        return set([]), set([]), currTracks

    # build list of track ids for the stormcells in the previous frame
    prevTracks = set([aCell['trackID'] for aCell in
                      stateHist[-1]['stormCells'] if aCell['trackID'] >= 0])


    # Find the set difference of the list of tracks.
    # The difference would be whatever tracks that existed in the previous
    # frame, but not in the current frame.
    tracksToEnd = prevTracks - currTracks

    # Now the opposite set difference.  These would be tracks
    # That exists in the current tracks, but not in the previous.
    tracksToAdd = currTracks - prevTracks

    # And now to see what remained the same.
    tracksToKeep = currTracks & prevTracks

    # Now end those tracks
    #    - Any tracks that are of length 2 or longer have
    #          their last storm cell marked as 'M' because
    #          it belonged to a track.
    #  Maybe some other tasks?
    for aTrackID in tracksToEnd :
        if len(strmTracks[aTrackID]) > 1 :
            # Mark the last storm cell in the track as "matched"
            strmTracks[aTrackID]['types'][-1] = 'M'
        else :
            # Mark a length-1 track as a False alarm.
            strmTracks[aTrackID]['types'][-1] = 'F'

    return tracksToEnd, tracksToKeep, tracksToAdd


def Correl_Storms(strmAdap, currStorms,
                  stateHist, strmTracks, infoTracks, deltaT) :

    newTracks = []
    contTracks = []
    distThresh = (strmAdap['spdThresh'] * deltaT) ** 2

    # Looping over the current storms to compare against the previous storms
    for newCell in currStorms :
        bestMatch = {'prevIndx': None, 
                     'dist': distThresh}

        #if len(infoTracks) != len(strmTracks) :
        #    print("WARNING in Correl_Storms()")

        for trackID, (infoTrack, track) in enumerate(zip(infoTracks,
                                                         strmTracks)) :
            # equal to 'U' means that storm hasn't been matched yet.
            if track['types'][-1] == 'U':
                """
                ### --- Outdated consistency check --- ###
                if track['frameNums'][-1] != (volTime - 1) :
                    print("WARNING! Expected frame num: ", volTime - 1)
                    print("New Cell:", newCell)
                    print("Old Cell:", track[-1])
                    continue
                """

                # Grab the forecasted location for the current point,
                # which can be found in its track's 'fcasts' element.
                cellDist = CalcDistSqrd(newCell,
                                        infoTrack['fcasts'][-1])
                if cellDist < bestMatch['dist'] :
                    bestMatch = {'prevIndx': trackID, 'dist': cellDist}


        if bestMatch['prevIndx'] is not None :
            # Note how it goes ahead and matches with the first storm cell
            # it finds that is below the threshold. I believe this to be
            # a bug that can cause "track-stealing" as the algorithm does
            # not find the closest stormcell, only the first one that was
            # "close enough". In other words, while this oldCell is the
            # closest oldCell to this newCell, it doesn't necessarially
            # mean that this newCell is the closest newCell to this oldCell.
            # This is *partly* mitigated by sorting the storm cells by size.
            # Larger storm cells supposedly have more stable centroids
            # (less noisey).  Track stealing more likely to occur with noisey
            # cell centroids. However, note that any sort of sorting must be
            # done outside of the SCIT tracking functions. In other words,
            # the passed-in storm cells should have already been sorted.

            #matchedStorm = prevStorms[bestMatch['prevIndx']]

            track = strmTracks[bestMatch['prevIndx']]

            # Indicate that the storm in the previous frame has
            # now been matched.
            track['types'][-1] = 'M'
            contTracks.append((newCell, bestMatch))

        else :
            # We did not find a suitable match, so we create a new track.
            # Give it the next available ID number.
            newTracks.append(newCell)


    for newCell, bestMatch in contTracks :
        trackID = bestMatch['prevIndx']

        track = strmTracks[trackID]
        infoTrack = infoTracks[trackID]

        infoTrack['distErrs'].append(np.sqrt(bestMatch['dist']))
        infoTrack['dists'].append(np.sqrt(CalcDistSqrd(newCell, track[-1])))

        # Assigning the current storm its track ID number, and
        # the state-estimated position
        newCell['trackID'] = trackID
        newCell['st_xLocs'] = infoTrack['fcasts'][-1]['xLocs']
        newCell['st_yLocs'] = infoTrack['fcasts'][-1]['yLocs']

        # Adding a new point to the established storm track
        strmTracks[trackID] = np.hstack((track, newCell))

    for aTrack in newTracks :
        # Assigning this track the next trackID number and
        # state-estimated position
        aTrack['trackID'] = len(strmTracks)
        aTrack['st_xLocs'] = aTrack['xLocs']
        aTrack['st_yLocs'] = aTrack['yLocs']
        # The forecast will be set later on.
        infoTracks.append({'distErrs': [0.0],
                           'dists': [0.0],
                           'fcasts': [],
                           'speed_x': [],
                           'speed_y': []})
        strmTracks.append(np.array([aTrack], dtype=volume_dtype))


def CalcDistSqrd(cellA, cellB) :
    return( (cellA['xLocs'] - cellB['xLocs'])**2 +
            (cellA['yLocs'] - cellB['yLocs'])**2 )


def BestLocs(stateHist, strmTracks, infoTracks, deltaT) :
    """
    Forecast where the active tracks will go.
    """
    # No need to do a forecast if the history is empty
    if len(stateHist) > 0 :
        # Look over all the storm cells in the previous frame.
        # Any storm cell that is part of an active track has a
        # positive trackID value.
        # Obtain unique set of active track IDs.
        trackIDs = set([stormCell['trackID'] for stormCell in
                        stateHist[-1]['stormCells'] if
                        stormCell['trackID'] >= 0])
        for index in trackIDs :
            info = infoTracks[index]
            strm = strmTracks[index]
            info['fcasts'].append({'xLocs': strm['xLocs'][-1] +
                                           (info['speed_x'][-1] * deltaT),
                                   'yLocs': strm['yLocs'][-1] +
                                           (info['speed_y'][-1] * deltaT)})



def Compute_Speed(strmAdap, currStorms, strmTracks, infoTracks,
                  deltaT, times, frameOffset=0) :
    """
    Updates the speed for all of the current, active tracks.
    Also initiates all new tracks with the average speed of all
    of the other active tracks.
    """
    tot_x_spd = 0.0
    tot_y_spd = 0.0
    trackCnt = 0
    framesBack = strmAdap['framesBack']

    # Gonna first calculate the track speed for all established tracks
    # in order to determine an overall average speed to use for initializing
    # the speed for un-established tracks.
    trackIDs = [stormCell['trackID'] for stormCell in currStorms if
                stormCell['trackID'] >= 0]
    #strmIDs = [stormCell['cornerIDs'] for stormCell in currStorms if
    #           stormCell['trackID'] >= 0]
    for index in trackIDs :

        theTrackInfo = infoTracks[index]
        aTrack = strmTracks[index][-framesBack:] \
                 if framesBack > 0 else \
                 strmTracks[index][0:0]     # return empty array

        if len(aTrack) > 1 :
            xAvg = np.mean(aTrack['xLocs'])
            yAvg = np.mean(aTrack['yLocs'])
            tAvg = np.mean(times[aTrack['frameNums'] - frameOffset])

            tDev = times[aTrack['frameNums'] - frameOffset] - tAvg
            xtVar = np.sum((aTrack['xLocs'] - xAvg) * tDev)
            ytVar = np.sum((aTrack['yLocs'] - yAvg) * tDev)
            ttVar = np.sum(tDev**2)

#            print("tot    tAvg:", tAvg, "   frames:", aTrack['frameNums'][-10:], "   ttVar: ", ttVar)
            tot_x_spd += (xtVar / ttVar)
            tot_y_spd += (ytVar / ttVar)
            trackCnt += 1

            theTrackInfo['speed_x'].append(xtVar / ttVar)
            theTrackInfo['speed_y'].append(ytVar / ttVar)

    if (trackCnt != 0) :
        systemAvg = {'speed_x': tot_x_spd / trackCnt,
                     'speed_y': tot_y_spd / trackCnt}
    else :
        direction = np.radians(strmAdap.get("default_dir", 0.0) + 180.0)
        speed = strmAdap.get("default_spd", 0.0)

        systemAvg = {'speed_x': speed * np.sin(direction),
                     'speed_y': speed * np.cos(direction)}

    #print("AVG SPEED: %8.5f  AVG DIRECTION: %6.2f" %
    #                 (np.hypot(systemAvg['speed_x'],
    #                           systemAvg['speed_y']) * (60.0 / 1.852),
    #                  (np.degrees(np.arctan2(systemAvg['speed_x'],
    #                                         systemAvg['speed_y'])) +
    #                   180.0) % 360.0))

    # Now initialize any unestablished tracks with the system average
    for index in trackIDs :
        theTrackInfo = infoTracks[index]
        if len(theTrackInfo['speed_x']) == 0 :
            theTrackInfo['speed_x'].append(systemAvg['speed_x'])
            theTrackInfo['speed_y'].append(systemAvg['speed_y'])

        #if len(theTrackInfo['speed_x']) != len(strmTracks[index]) :
        #    print("WARNING! Track len doesn't match trackinfo len!", index)

if __name__ == '__main__' :
    import os.path
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

    from ZigZag.TrackPlot import PlotPlainTracks, PlotSegments
    from ZigZag.TrackUtils import CleanupTracks, FilterMHTTracks,\
                                  CreateSegments, CompareSegments
    from ZigZag.TrackFileUtils import ReadCorners, ReadTracks

    dirPath = "/home/ben/Programs/Tracking/NewSim1"
    #dirPath = "/home/bvr/TrackingStudy/SquallSim"
    cornerVol = ReadCorners(os.path.join(dirPath, "InputDataFile"),
                            dirPath)['volume_data']

    true_tracks, true_falarms = FilterMHTTracks(*ReadTracks(os.path.join(
                                                    dirPath, "noise_tracks")))

    frameLims = (0, len(cornerVol))
    strmAdap = {'spdThresh': 5.0,
                'framesBack': 10,
                'default_spd': 1.0,
                'default_dir': 225.0,
                'max_timestep': 15.0}
    stateHist = []
    strmTracks = []
    infoTracks = []

    deltaT = cornerVol[1]['volTime'] - cornerVol[0]['volTime']
    frameOffset = cornerVol[0]['frameNum']

    for aVol in cornerVol :
        TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol,
                       deltaT, frameOffset)

    EndTracks(stateHist, strmTracks)

    falarms = []
    tracks = strmTracks
    CleanupTracks(tracks, falarms)

    # Compare with "truth data"
    segs = [CreateSegments(trackData) for trackData in (true_tracks,
                                                        true_falarms,
                                                        tracks, falarms)]
    truthtable = CompareSegments(*segs)


    # Display Result
    fig = plt.figure(figsize=plt.figaspect(0.5))
    grid = AxesGrid(fig, 111, nrows_ncols=(1, 2), aspect=False,
                    share_all=True, axes_pad=0.35)

    ax = grid[0]
    PlotPlainTracks(tracks, falarms, *frameLims, axis=ax)
    ax.set_title("SCIT Tracks")

    ax = grid[1]
    PlotSegments(truthtable, frameLims, axis=ax)
    ax.set_title("Track Check")

    plt.show()


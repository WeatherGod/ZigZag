from ZigZag.TrackUtils import volume_dtype
import numpy as np
import numpy.lib.recfunctions as nprf   # for append_fields()
from scikits.learn.utils.hungarian import hungarian

bad_cost = 9999999.0
bad_thresh = 5.0

def calc_cost(t0_strms, t1_strms) :
    x0 = t0_strms['xLocs']
    x1 = t1_strms['xLocs']

    y0 = t0_strms['yLocs']
    y1 = t1_strms['yLocs']

    C = np.hypot(x0[:, np.newaxis] - x1[np.newaxis, :],
                 y0[:, np.newaxis] - y1[np.newaxis, :])

    return np.where(C > bad_thresh, bad_cost, C)

def reject_assoc(cost_val) :
    # Reject this association because they were too far apart
    return cost_val >= bad_thresh

def process_assocs(assocs, cost, currStrmCnt, prevStorms) :
    strms_end = {}
    strms_start = {}
    strms_keep = {}

    for t0_index, t1_index in enumerate(assocs) :
        if reject_assoc(cost[t0_index, t1_index]) :
            # Because of the rejection, split this
            # association into the termination of
            # one track and the start of a new track
            strms_end[t0_index] = prevStorms[t0_index]
            # TrackID will be assigned when the track is created
            strms_start[t1_index] = None
        else :
            strms_keep[t1_index] = prevStorms[t0_index]
    
    # Determine which other current storms were not associated
    # This happens when there are more current storms than previous storms
    newstorms = set(range(currStrmCnt)) - set(assocs)
    strms_start.update(zip(newstorms, [None]*len(newstorms)))

    #currTracks = set(strms_keep.values())
    #prevTracks = set(prevStrms.values())
    #tracks_end = prevTracks - currTracks
    #tracks_start = currTracks - prevTracks
    #tracks_keep = currTracks & prevTracks

    return strms_end, strms_keep, strms_start

def update_tracks(tracks, currStrms, currFrame, strms_end, strms_keep, strms_start) :

    # Only need to do the following if I and adding or extending
    # existing tracks
    if len(strms_keep) > 0 or len(strms_start) > 0 :
        # The volume data has only xLocs and yLocs,
        # so we need to add some track-relevant fields
        # to the data without modifying the input data.
        strmCnt = len(currStrms)
        currStrms = nprf.append_fields(currStrms,
                                       ('frameNums', 'types', 'trackID'),
                                       ([currFrame] * strmCnt,
                                        ['U'] * strmCnt,
                                        [-1] * strmCnt),
                                       usemask=False)


    for strmID, trackID in strms_keep.iteritems() :
        # A poor-man's append for numpy arrays...
        #currStrms[strmID]['types'] = 'M'
        currStrms[strmID]['trackID'] = trackID
        # Update the last storm cell listed in the track as matched
        tracks[trackID]['types'][-1] = 'M'
        tracks[trackID] = np.hstack((tracks[trackID], currStrms[strmID]))

    for strmID in strms_start.keys() :
        trackID = len(tracks)
        strms_start[strmID] = trackID
        #currStrms[strmID]['types'] = 'M'
        currStrms[strmID]['trackID'] = trackID
        tracks.append(np.array([currStrms[strmID]], dtype=volume_dtype))

    # Mark any length-1 tracks for strms_end as False Alarms
    for trackID in strms_end.values() :
        if len(tracks[trackID]) == 1 :
            tracks[trackID]['types'][-1] = 'F'
        else :
            tracks[trackID]['types'][-1] = 'M'

def TrackStep_TITAN(trackerParams, stateHist, strmTracks, volume_data, prevStorms) :
    bad_cost = trackerParams['distThresh']

    if len(stateHist) > 0 :
        prevCells = stateHist[-1]['stormCells']
    else :
        prevCells = np.array([], dtype=volume_dtype)

    currCells = volume_data['stormCells']
    frameNum = volume_data['frameNum']

    C = calc_cost(prevCells, currCells)
    assocs = hungarian(C)
    
    # Maybe something for infoTracks?

    # Return the storms organized by their status.
    # strms_end  :  dict of storm indices for storms at index-1 with value trackID
    # strms_keep :  dict of storm indices for storms at index with value trackID
    # strms_start:  dict of storm indices for storms at index with value trackID
    strms_end, strms_keep, strms_start = process_assocs(assocs, C, len(currCells), prevStorms)

    update_tracks(strmTracks, currCells, frameNum,
                  strms_end, strms_keep, strms_start)

    # The union of tracks that were kept and started for the next loop iteration.
    prevStorms = strms_keep.copy()
    prevStorms.update(strms_start)

    stateHist.append({'volTime': volume_data['volTime'],
                      'frameNum': volume_data['frameNum'],
                      'stormCells': volume_data['stormCells']})

    return strms_end, strms_keep, strms_start


if __name__ == '__main__' :
    import os.path
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

    from ZigZag.TrackPlot import PlotPlainTracks, PlotSegments
    from ZigZag.TrackUtils import CleanupTracks, FilterMHTTracks,\
                                  CreateSegments, CompareSegments
    from ZigZag.TrackFileUtils import ReadCorners, ReadTracks

    #dirPath = "/home/ben/Programs/Tracking/NewSim1"
    dirPath = "/home/bvr/TrackingStudy/SquallSim"
    cornerVol = ReadCorners(dirPath + os.path.sep + "InputDataFile",
                            dirPath)['volume_data']

    true_tracks, true_falarms = FilterMHTTracks(*ReadTracks(dirPath + os.path.sep + "noise_tracks"))

    tracks = []
    prevStorms = {}
    trackParams = {'distThresh': 5}
    stateHist = []

    frameLims = (0, len(cornerVol))
    print frameLims[1]

    for aVol in cornerVol :
        results = TrackStep_TITAN(trackParams, stateHist, tracks, aVol, prevStorms)
        prevStorms = results[1].copy()
        prevStorms.update(results[2])

    # Finalize tracks
    update_tracks(tracks, None, None, prevStorms, {}, {})

    falarms = []
    CleanupTracks(tracks, falarms)


    # Compare with "truth data"
    segs = [CreateSegments(trackData) for trackData in (true_tracks, true_falarms,
                                                    tracks, falarms)]
    truthtable = CompareSegments(*segs)


    # Display Result
    fig = plt.figure(figsize=plt.figaspect(0.5))
    grid = AxesGrid(fig, 111, nrows_ncols=(1, 2), aspect=False,
                    share_all=True, axes_pad=0.35)

    ax = grid[0]
    PlotPlainTracks(tracks, falarms, *frameLims, axis=ax)
    ax.set_title("TITAN Tracks")

    ax = grid[1]
    PlotSegments(truthtable, frameLims, axis=ax)
    ax.set_title("Track Check")

    plt.show()


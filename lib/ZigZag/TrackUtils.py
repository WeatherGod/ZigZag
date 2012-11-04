from __future__ import print_function
import math
import numpy as np
import numpy.lib.recfunctions as nprf		# for .stack_arrays(), .append_fields()
from scipy.spatial import KDTree

# The following are used to specify the dtype of various
# numpy record arrays.

# The position of a centroid
pos_dtype = [('xLocs', 'f4'), ('yLocs', 'f4')]

# "Texture" data -- extra information about the object
# represented by the centroid.  Currently, we have "sizes"
# which is the size of the stormcell in volume units.
texture_dtype = [('sizes', 'f4')]

# A (hopefully) unique identifier for each detected feature
cornerID_dtype = [('cornerIDs', 'i4')]

# "frameNums" is the 'time' of the detected feature in units
# of the frame index. "type" indicates what status the feature
# was given by the tracker (or simulator).
# 'st_xLocs' and 'st_yLocs' are for the state-estimated
# x and y locations (estimated by the tracker).
tracking_dtype = [('st_xLocs', 'f4'), ('st_yLocs', 'f4'),
                  ('frameNums', 'i4'), ('types', 'a1')]

# A (hopefully) unique track identifier for each determined track
# Note that -1 indicates that the feature is not a track.
identifier_dtype = [('trackID', 'i4')]

corner_dtype = pos_dtype + texture_dtype + cornerID_dtype
base_track_dtype = pos_dtype + cornerID_dtype + tracking_dtype
track_dtype = corner_dtype + tracking_dtype
volume_dtype = track_dtype + identifier_dtype

def Tracks2Cells(tracks, falarms=None) :
    """
    Convert lists of tracks (and falarms) into a single recarray of storm cells
    with track IDs.

    This can be reversed with Cells2Tracks().
    """
    if falarms is None :
        falarms = []

    # NOTE: This function can not handle arrays of tracks that do/do not have
    #       a trackID field in a mix.  Either they all have it, or not.
    if not any('trackID' in aTrack.dtype.names for aTrack in tracks) :
        tracks = [nprf.append_fields(aTrack, 'trackID',
                                     [trackIndex] * len(aTrack),
                                     usemask=False)
                  for trackIndex, aTrack in enumerate(tracks)]

    if not any('trackID' in aTrack.dtype.names for aTrack in falarms) :
        falarms = [nprf.append_fields(aTrack, 'trackID',
                                      [-trackIndex - 1] * len(aTrack),
                                      usemask=False)
                   for trackIndex, aTrack in enumerate(falarms)]

    # If both are empty, then create an array without hstack()
    if len(tracks) != 0 or len(falarms) != 0 :
        allCells = np.hstack(tracks + falarms)
    else :
        allCells = np.array([], dtype=volume_dtype)

    return allCells


def Cells2Tracks(strmCells) :
    """
    Convert a numpy recarray of dtype track_dtype into two lists
    of tracks and falarms.

    This can be reversed with Tracks2Cells().
    """
    trackIDs = np.unique(strmCells['trackID'][strmCells['trackID'] >= 0])
    tracks = [np.sort(strmCells[strmCells['trackID'] == id], 0, order=['frameNums'])
                for id in trackIDs]

    falarmIDs = np.unique(strmCells['trackID'][strmCells['trackID'] < 0])    
    falarms = [np.sort(strmCells[strmCells['trackID'] == id], 0, order=['frameNums'])
                for id in falarmIDs]

    return tracks, falarms
    

def CreateVolData(tracks, falarms, frames, tLims=None, xLims=None, yLims=None) :
    """
    Essentially, go from lagrangian (following a particle)
    to eulerian (at fixed points on a grid).

    Note that this method will retain the 'trackID' number,
    so it is possible to reconstruct the (clipped) track data using
    this output.
    """

    allCells = Tracks2Cells(tracks, falarms)
    return Cells2VolData(allCells, frames,
                         tLims=tLims, xLims=xLims, yLims=yLims)


def Cells2VolData(allCells, frames, tLims=None, xLims=None, yLims=None) :
    """
    Convert a flat numpy array of dtype volume_dtype into a list of
    dicts (one for each frame). The dicts contain the frame index, volume time,
    and the storm cells.
    """
    volData = []
    # Note, this is a mask in the opposite sense from a numpy masked array.
    #       True means that this is a value to keep.
    xMask = ((allCells['xLocs'] >= min(xLims)) &
             (allCells['xLocs'] <= max(xLims))) if xLims is not None else True

    yMask = ((allCells['yLocs'] >= min(yLims)) &
             (allCells['yLocs'] <= max(yLims))) if yLims is not None else True

    domainMask = (xMask & yMask)

    times = frames if tLims is None else \
            np.linspace(min(tLims), max(tLims), len(frames))

    for volTime, frameIndex in zip(times, frames) :
        # Again, this mask is opposite from numpy masked array.
        tMask = (allCells['frameNums'] == frameIndex)
        volData.append({'volTime': volTime,
                        'frameNum': frameIndex,
                        'stormCells': allCells[domainMask & tMask]})

    return volData


def ClipTracks(tracks, falarms, xLims, yLims, frameLims) :
    """
    Return a copy of the tracks and falarms, clipped to within
    the given domain.

    All tracks clipped to length of one are moved to a copy of falarms.
    """
    # Note, this is a mask in the opposite sense from a numpy masked array.
    #       Here, True means that this is a value to keep.
    clippedTracks = [ClipTrack(aTrack, xLims, yLims, frameLims) for aTrack in tracks]
    clippedFAlarms = [ClipTrack(aTrack, xLims, yLims, frameLims) for aTrack in falarms]

    CleanupTracks(clippedTracks, clippedFAlarms)
#    print("Length of tracks outside: ", len(clippedTracks))
    return clippedTracks, clippedFAlarms

def ClipTrack(track, xLims, yLims, frameLims) :
    domainMask = np.logical_and(track['xLocs'] >= min(xLims),
                 np.logical_and(track['xLocs'] <= max(xLims),
                 np.logical_and(track['yLocs'] >= min(yLims),
                 np.logical_and(track['yLocs'] <= max(yLims),
                 np.logical_and(track['frameNums'] >= min(frameLims),
                                track['frameNums'] <= max(frameLims))))))

    return track[domainMask]

def FilterTrack(track, frames=None, **kwargs) :
    """
    Filter a track.

    *kwargs* is a dictionary keyed by the name of the data to be compared
             and the value is the list of valid values to keep that particular
             part of the track.

    *frames* is for backwards-compatibility (was a position argument)
             and is equivalent to using 'frameNums' as a key.

    Example:
        track = FilterTrack(track, frameNums=frames)
    """
    if frames is not None :
        kwargs['frameNums'] = frames

    mask = np.ones((len(track),), dtype=bool)
    for key, vals in kwargs.iteritems() :
        mask &= np.array([(aFrame[key] in vals) for
                          aFrame in track],
                          dtype=bool)

    return track[mask]

def ReplaceFrameInfo(tracks, replaceFrames) :
    """
    Replace the value of frameNums in the track with a new frame number
    according to the mapping provided by the *replaceFrames* dictionary.

    *tracks*        List of tracks
    *replaceFrames* Dictionary keyed by the original framenumbers with
                    replacement frame numbers set as the paired value.
    """
    for aTrack in tracks :
        aTrack['frameNums'][:] = [replaceFrames[frame] for frame in
                                  aTrack['frameNums']]

def CleanupTracks(tracks, falarms) :
    """
    Moves tracks that were shortened to single length to the
    falarms list, and eliminate the empty tracks.
    """

    for trackIndex in range(len(tracks))[::-1] :
        if len(tracks[trackIndex]) == 1 :
            #print("Cleanup:", tracks[trackIndex])
            # Change the type to a False Alarm
            tracks[trackIndex]['types'][0] = 'F'
            falarms.append(tracks[trackIndex])
            tracks[trackIndex] = []

        if len(tracks[trackIndex]) == 0 :
            del tracks[trackIndex]

    for trackIndex in range(len(falarms))[::-1] :
        if len(falarms[trackIndex]) == 0 :
            del falarms[trackIndex]


def FilterSegments(idKeepers, segs) :
    """
    Filter a list of segments based on the cornerID value of the segment's
    start point. *idKeepers* contains the cornerID values that are to be
    kept.  If it is None, no filtering is done.

    *others* are additional lists that may be parallel to *segs* and should
    be filtered as well based on the results of comparison to *segs*. This
    is intended for the "trackIndices" that can be returned by
    :func:`CreateSegments`.
    """
    if idKeepers is None :
        return segs
#        return segs, *others

    segs = [aSeg for aSeg in segs if aSeg[0]['cornerIDs'] in idKeepers]

    return segs


def CreateSegments(tracks, retindices=False, lastFrame=None) :
    """
    Breaks up a list of the tracks (or falarms) into an array of segments.
    Each element in the arrays represents the start and end point of a segment.

    If you want to impose a finite timeline, and therefore, exclude
    any segments that start on or after *lastFrame*.
    """
    segs = []
    indices = []
    for trackID, aTrack in enumerate(tracks) :
        if len(aTrack) > 1 :
            tmpSegs = [np.hstack(aSeg) for aSeg in zip(aTrack[:-1],
                                                       aTrack[1:]) if
                       (lastFrame is None or
                        aSeg[0]['frameNums'] < lastFrame)]
            segs.extend(tmpSegs)
            indices.extend([trackID] * len(tmpSegs))

        if lastFrame is None or aTrack[-1]['frameNums'] < lastFrame :
            segs.append(aTrack[-1:])
            indices.append(trackID)

    if retindices :
        return segs, indices
    else :
        return segs

def Segs2Tracks(truthTable, trackIndices, falarmIndices) :
    """
    From the truth table data structure, and the indices from CreateSegments,
    we have the technology to rebuild the tracks, make it better, faster.

    (well, maybe not faster...)

    The function returns an index list for each bin in the truthTable
    that maps a segment to the track/falarm it came from
    """
    corrAssocsLen = len(truthTable['assocs_Correct'])

    corr_segs2tracks = [trackIndices[segIndex] for segIndex in
                        truthTable['correct_indices'][0:corrAssocsLen]]
    corr_segs2falarms = [falarmIndices[segIndex] for segIndex in
                         truthTable['correct_indices'][corrAssocsLen:]]

    wrngAssocsLen = len(truthTable['assocs_Wrong'])
    wrng_segs2tracks = [trackIndices[segIndex] for segIndex in
                        truthTable['wrong_indices'][0:wrngAssocsLen]]
    wrng_segs2falarms = [falarmIndices[segIndex] for segIndex in
                         truthTable['wrong_indices'][wrngAssocsLen:]]

    return {'corr2tracks': corr_segs2tracks, 'corr2falarms': corr_segs2falarms,
            'wrng2tracks': wrng_segs2tracks, 'wrng2falarms': wrng_segs2falarms}



def PrintTruthTable(truthTable) :
    """
    Print out the truth table (a.k.a. - contingency table) for the line
    segments that was generated by CompareSegments().
    """
    print("""
                                Reality
             |        True         |        False        ||
  Predicted  |                     |                     ||
 ============+=====================+=====================||
             | Correct Association |  Wrong Association  ||
    True     |        %5d        |        %5d        ||
             |                     |                     ||
 ------------+---------------------+---------------------+|
             |   Wrong Non-Assoc.  | Correct Non-Assoc.  ||
    False    |        %5d        |        %5d        ||
             |                     |                     ||
 ========================================================//
""" % (len(truthTable['assocs_Correct']), len(truthTable['assocs_Wrong']),
       len(truthTable['falarms_Wrong']), len(truthTable['falarms_Correct'])))

def MakeTruthTable(realSegs, realFAlarmSegs, predSegs, predFAlarmSegs) :
    """
    Revamped version of CompareSegments().  I am not willing to replace
    CompareSegments() yet because it is valuable in producing the data
    necessary to display the track plots (although it still needs fixing...).

    This method will be a mathematically, margin-sum correct
    method of creating a contingency table, however it is not
    useful for producing track plots.
    """
    # Do comparisons between the real track segments and
    # the predicted segments.
    (assocs_Correct,
     assocs_Wrong,
     assocs_Correct_indices,
     assocs_Wrong_indices) = _compare_segs(realSegs, predSegs)

    # Now, do comparisons between the real false alarms and the
    # predicted false alarms.
    (falarms_Correct,
     falarms_Wrong,
     falarms_Correct_indices,
     falarms_Wrong_indices) = _compare_segs(realFAlarmSegs, predFAlarmSegs)

    return {'assocs_Correct': assocs_Correct,
            'assocs_Wrong': assocs_Wrong,
            'falarms_Wrong': falarms_Wrong,
            'falarms_Correct': falarms_Correct,
            'correct_indices': assocs_Correct_indices + falarms_Correct_indices,
            'wrong_indices': assocs_Wrong_indices + falarms_Wrong_indices}

def MakeContingency(obvSegs, trkSegs) :
    """
    Revamped version of :func:`MakeTruthTable`.  I am not willing
    to replace 'MakeTruthTable' until I fully understand the implications
    with this second revamp.

    This method will be a mathematically, margin-sum correct
    method of creating a contingency table, however it is not
    useful for producing track plots.
    """
    if len(obvSegs) != len(trkSegs) :
        print("WARNING: Segment count mismatch: " \
              "%d vs. %d" % (len(obvSegs), len(trkSegs)))

    # Create a dictionary to map the cornerID for the first
    # part of each tracking segment to the index number
    # in the trkSegs list.
    mapper = {}
    for i, aSeg in enumerate(trkSegs) :
        mapper[aSeg['cornerIDs'][0]] = i

    # Dictionaries mapped to tuples of bools: (isAssoc, isCorrect)
    # (True, True) == Correct Association
    # (True, False) == Incorrect Association
    # (False, True) == Correct Non-Association
    # (False, False) == Incorrect Non-Association
    segs = {(True, True) : [], (True, False) : [],
            (False, True): [], (False, False): []}
    seg_indices = {(True, True) : [], (True, False) : [],
                   (False, True): [], (False, False): []}

    # Now, go through each observed segments, seeking out
    # the trkSeg that has the same cornerID for the first
    # part of the segment as the obvserved segment.
    # Then compare the cornerID of the last part of the
    # observed segment with the last part of the tracking
    # segment.
    # Note that I am not saying to match against the second
    # part, because some segments can be of length one.
    #
    # If the length of the observed segment do not
    # match the length of the tracking segment, that's
    # ok because the second part of the longer segment
    # will never have the same cornerID as the first
    # part of the shorter segment, because the corner
    # ids for a segment are never the same, and the
    # corner id for the first part already matched the
    # corner id of the short segment.
    for i, aSeg in enumerate(obvSegs) :
        is_assoc = (len(aSeg) == 2)
        obv_corners = aSeg['cornerIDs']
        trkseg_id = mapper[obv_corners[0]]
        trk_corners = trkSegs[trkseg_id]['cornerIDs']
        is_correct = (obv_corners[-1] == trk_corners[-1])

        segs[(is_assoc, is_correct)].append(aSeg)
        seg_indices[(is_assoc, is_correct)].append(trkseg_id)

    return {'assocs_Correct': segs[(True, True)],
            'assocs_Wrong': segs[(True, False)],
            'falarms_Wrong': segs[(False, False)],
            'falarms_Correct': segs[(False, True)],
            'assocs_should': seg_indices[(True, False)],
            'falarms_should': seg_indices[(False, False)]}
   

def _compare_segs(realSegs, predSegs) :
    """
    Convenience function to keep code clean and consistent.
    This code takes segment data and (quickly) determines
    which of the real segments has a matching predicted
    segment.
    """

    predData = [(aSeg['xLocs'][0], aSeg['yLocs'][0]) for aSeg in predSegs]
    realData = [(aSeg['xLocs'][0], aSeg['yLocs'][0]) for aSeg in realSegs]

    correct = []
    correct_indices = []
    wrong = []
    wrong_indices = []


    if len(predData) > 0 and len(realData) > 0 :
        predTree = KDTree(predData)
        
        # closestIndicies will have length equal to the length of realData.
        # In other words, for each point in realData, the closest point in predData
        # will be provided.
        dists, closestIndicies = predTree.query(realData)

        # Now, see if the closest point matches the real point
        for realIndex, (predIndex, realPoint) in enumerate(zip(closestIndicies, realSegs)) :
            if is_eq(realPoint, predSegs[predIndex]) :
                correct.append(realPoint)
                correct_indices.append(realIndex)
            else :
                wrong.append(realPoint)
                wrong_indices.append(realIndex)
    else :
        # For whatever reason (no real data, or no predicted data),
        # we can't make any comparisons.  But, this does mean that any
        # real trackings that existed were completely missed.
        wrong = [aSeg for aSeg in realSegs]
        wrong_indices = range(len(realSegs))

    return correct, wrong, correct_indices, wrong_indices



def CompareSegments(realSegs, realFAlarmSegs, predSegs, predFAlarmSegs) :
    """
    This function will compare the line segments and false alarm points and
    categorize them based upon a truth table.  The truth table will determine
    if the proper point associations were made.

                                Reality
                 |      True       |      False      |
     Predicted   |                 |                 |
    -------------+-----------------+-----------------+
        True     |  assocs_Correct |  assocs_Wrong   |
    -------------+-----------------+-----------------+
       False     |  falarms_Wrong  | falarms_Correct |
    -------------+-----------------+-----------------+
    """
    trkSegs = realSegs + realFAlarmSegs
    trkSegs_results = MakeContingency(predSegs + predFAlarmSegs,
                                      realSegs + realFAlarmSegs)

    missed = []
    for segID in (trkSegs_results['assocs_should'] +
                  trkSegs_results['falarms_should']) :
        if len(trkSegs[segID]) == 2 :
            missed.append(trkSegs[segID])

    return {'assocs_Correct': trkSegs_results['assocs_Correct'],
            'assocs_Wrong': trkSegs_results['assocs_Wrong'],
            'falarms_Wrong': trkSegs_results['falarms_Wrong'] + missed,
            'falarms_Correct': trkSegs_results['falarms_Correct']}



def FilterMHTTracks(origTracks, origFalarms) :
    """
    This function will 'clean up' the track output from ReadTracks()
    such that the tracks contain only the actual detected points.
    Also, it will move any one-length tracks to falarms, and completely
    remove any zero-length tracks.
    """
    tracks = [aTrack.copy() for aTrack in origTracks]
    falarms = [aTrack.copy() for aTrack in origFalarms]

    for trackIndex, aTrack in enumerate(tracks) :
        tracks[trackIndex] = aTrack[aTrack['types'] == 'M']

    CleanupTracks(tracks, falarms)
    return tracks, falarms


def DomainFromTracks(tracks, falarms=None) :
    """
    Calculate the spatial and temporal domain of the tracks and false alarms.
    Note that this assumes that bad points are non-existant or has been
    masked out.
    """
    if falarms is None :
        falarms = []

    # FIXME: This will fail if both arrays are empty, but in which case,
    #        what should the return values be anyway?
    allPoints = np.hstack(tracks + falarms)
    
    return ((allPoints['xLocs'].min(), allPoints['xLocs'].max()),
            (allPoints['yLocs'].min(), allPoints['yLocs'].max()),
            (allPoints['frameNums'].min(), allPoints['frameNums'].max()))

def DomainFromVolumes(volumes) :
    """
    Calculate the spatial and temporal domain of the volume data.
    Assumes that bad points are non-existant or has been masked out.
    """
    # FIXME: This will fail if volumes is empty, but in which case,
    #        what should the return values be anyway?
    allPoints = np.hstack([volData['stormCells'] for volData in volumes])
    allFrames = [volData['frameNum'] for volData in volumes]
    allTimes = [volData['volTime'] for volData in volumes]

    return ((allPoints['xLocs'].min(), allPoints['xLocs'].max()),
            (allPoints['yLocs'].min(), allPoints['yLocs'].max()),
            (min(allTimes), max(allTimes)),
            (min(allFrames), max(allFrames)))

def ForecastTracks(tracks) :
    """
    Experimental function that would allow a quick-n-dirty forecast
    of feature position based upon supplied track data.

    *tracks*        List of tracks
    """
    fcast_tracks = [None] * len(tracks)

    for index, aTrack in enumerate(tracks) :
        fcast = np.empty_like(aTrack)
        # Persistance model
        fcast[0:2] = aTrack[0]

        if len(aTrack) < 3 :
            fcast_tracks[index] = fcast
            continue

        dx = np.diff(zip(aTrack['xLocs'], aTrack['yLocs']), axis=0)
        df = np.diff(aTrack['frameNums'], axis=0)

        fcast['xLocs'][2:] = aTrack['xLocs'][1:-1] + (dx[:-1, 0] * df[:-1])
        fcast['yLocs'][2:] = aTrack['yLocs'][1:-1] + (dx[:-1, 1] * df[:-1])
        fcast_tracks[index] = fcast

    return fcast_tracks

def is_eq(seg1, seg2) :
    """
    Yeah, I know this isn't the smartest thing I have done, but
    most of my code only needs float type math, and it would be
    far to difficult to convert all of the models and such over
    to the "new" decimal type.
    Instead, I just worry about equality with respect to about
    6 decimal places, which is how I am dealing with it for now.

    TODO: Come up with a better way!

    Maybe tag storm cells with id numbers and get the trackers to carry those tags through?
    """
#    return int(round(val1 * 1000., 1)) == int(round(val2 * 1000., 1))
#    return np.all(np.hstack((np.abs(seg1['xLocs'] - seg2['xLocs']) < 0.00000001,
#                                   np.abs(seg1['yLocs'] - seg2['yLocs']) < 0.00000001,
#                                   seg1['frameNums'] == seg2['frameNums'])))
    return np.all(seg1['cornerIDs'] == seg2['cornerIDs'])

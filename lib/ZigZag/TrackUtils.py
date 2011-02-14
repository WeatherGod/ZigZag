import math
import numpy as np
import numpy.lib.recfunctions as nprf		# for .stack_arrays(), .append_fields()
from scipy.spatial import KDTree

corner_dtype = [('xLocs', 'f4'), ('yLocs', 'f4'), ('cornerIDs', 'i4')]
track_dtype = corner_dtype + [('frameNums', 'i4'), ('types', 'a1')]
volume_dtype = track_dtype + [('trackID', 'i4')]
#storm_dtype = track_dtype + [('types', 'a1'), ('frameNums', 'i4'), ('trackID', 'i4')]

def Tracks2Cells(tracks, falarms=None) :
    """
    Convert lists of tracks (and falarms) into a single recarray of storm cells
    with track IDs.

    This can be reversed with Cells2Tracks().
    """
    if falarms is None :
        falarms = []

    tmpTracks = [nprf.append_fields(aTrack, 'trackID',
                                    [trackIndex] * len(aTrack),
                                    usemask=False)
                      for trackIndex, aTrack in enumerate(tracks)]

    tmpFalarms = [nprf.append_fields(aTrack, 'trackID',
                                     [-trackIndex - 1] * len(aTrack),
                                     usemask=False)
                      for trackIndex, aTrack in enumerate(falarms)]

    if len(tmpTracks) != 0 or len(tmpFalarms) != 0 :
        allCells = np.hstack(tmpTracks + tmpFalarms)
    else :
        allCells = np.array([], dtype=track_dtype)

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
                for id in trackIDs]

    return tracks, falarms
    

def CreateVolData(tracks, falarms, frames, tLims, xLims, yLims) :
    """
    Essentially, go from lagrangian (following a particle)
    to eulerian (at fixed points on a grid).

    Note that this method will retain the 'trackID' number,
    so it is possible to reconstruct the (clipped) track data using
    this output.
    """
    volData = []
    allCells = Tracks2Cells(tracks, falarms)

    # Note, this is a mask in the opposite sense from a numpy masked array.
    #       True means that this is a value to keep.
    domainMask = np.logical_and(allCells['xLocs'] >= min(xLims),
                 np.logical_and(allCells['xLocs'] <= max(xLims),
                 np.logical_and(allCells['yLocs'] >= min(yLims),
                                allCells['yLocs'] <= max(yLims))))

    times = np.linspace(min(tLims), max(tLims), len(frames))

    for volTime, frameIndex in zip(times, frames) :
        # Again, this mask is opposite from numpy masked array.
        tMask = (allCells['frameNums'] == frameIndex)
        volData.append({'volTime': volTime,
                        'frameNum': frameIndex,
                        'stormCells': allCells[np.logical_and(domainMask, tMask)]})

    return(volData)


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
#    print "Length of tracks outside: ", len(clippedTracks)
    return clippedTracks, clippedFAlarms

def ClipTrack(track, xLims, yLims, frameLims) :
    domainMask = np.logical_and(track['xLocs'] >= min(xLims),
                 np.logical_and(track['xLocs'] <= max(xLims),
                 np.logical_and(track['yLocs'] >= min(yLims),
                 np.logical_and(track['yLocs'] <= max(yLims),
                 np.logical_and(track['frameNums'] >= min(frameLims),
                                track['frameNums'] <= max(frameLims))))))

    return track[domainMask]

def FilterTrack(track, frames) :
    mask = np.array([(aFrame['frameNums'] in frames)
                     for aFrame in track],
                    dtype=bool)
    return track[mask]

def CleanupTracks(tracks, falarms) :
    """
    Moves tracks that were shortened to single length to the
    falarms list, and eliminate the empty tracks.
    """

    for trackIndex in range(len(tracks))[::-1] :
        if len(tracks[trackIndex]) == 1 :
            #print "Cleanup:", tracks[trackIndex]
            # Change the type to a False Alarm
            tracks[trackIndex]['types'][0] = 'F'
            falarms.append(tracks[trackIndex])
            tracks[trackIndex] = []

        if len(tracks[trackIndex]) == 0 :
            del tracks[trackIndex]

    for trackIndex in range(len(falarms))[::-1] :
        if len(falarms[trackIndex]) == 0 :
            del falarms[trackIndex]




def CreateSegments(tracks) :
    """
    Breaks up a list of the tracks (or falarms) into an array of segments.
    Each element in the arrays represents the start and end point of a segment.
    """
    segs = []
    for aTrack in tracks :
        trackLen = len(aTrack)
        if trackLen > 1 :
            segs.extend([np.hstack(aSeg) for aSeg in zip(aTrack[0:trackLen - 1],
                                                         aTrack[1:trackLen])])
        elif trackLen == 1 :
            segs.append(aTrack)

    return segs


def PrintTruthTable(truthTable) :
    """
    Print out the truth table (a.k.a. - contingency table) for the line
    segments that was generated by CompareSegments().
    """
    print """
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
       len(truthTable['falarms_Wrong']), len(truthTable['falarms_Correct']))

def MakeTruthTable(realSegs, realFAlarmSegs, predSegs, predFAlarmSegs) :
    """
    Revamped version of CompareSegments().  I am not willing to replace
    CompareSegments() yet because it is valuable in producing the data
    necessary to display the track plots (although it still needs fixing...).

    This method will be a mathematically, margin-sum correct method of creating
    a contingency table, however it is not useful for producing track plots.
    """
    # Do comparisons between the real track segments and
    # the predicted segments.
    assocs_Correct, assocs_Wrong = _compare_segs(realSegs, predSegs)

    # Now, do comparisons between the real false alarms and the
    # predicted false alarms.
    falarms_Correct, falarms_Wrong = _compare_segs(realFAlarmSegs, predFAlarmSegs)

    return {'assocs_Correct': assocs_Correct, 'assocs_Wrong': assocs_Wrong,
            'falarms_Wrong': falarms_Wrong, 'falarms_Correct': falarms_Correct}
    

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
    wrong = []

    if len(predData) > 0 and len(realData) > 0 :
        predTree = KDTree(predData)
        
        # closestIndicies will have length equal to the length of realData.
        # In other words, for each point in realData, the closest point in predData
        # will be provided.
        dists, closestIndicies = predTree.query(realData)

        # Now, see if the closest point matches the real point
        for predIndex, realPoint in zip(closestIndicies, realSegs) :
            if is_eq(realPoint, predSegs[predIndex]) :
                correct.append(realPoint)
            else :
                wrong.append(realPoint)
    else :
        # For whatever reason (no real data, or no predicted data),
        # we can't make any comparisons.  But, this does mean that any
        # real trackings that existed were completely missed.
        wrong = [aSeg for aSeg in realSegs]

    return correct, wrong



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
    assocs_Correct = []
    falarms_Correct = []
    assocs_Wrong = []
    falarms_Wrong = []

    unmatchedPredTrackSegs = range(len(predSegs))

    if len(predSegs) > 0 :
        predTree = KDTree([(aSeg['xLocs'][0], aSeg['yLocs'][0]) for aSeg in predSegs])
        trueData = [(aSeg['xLocs'][0], aSeg['yLocs'][0]) for aSeg in realSegs]

        if len(realSegs) > 0 :
            closestMatches = predTree.query(trueData)
        else :
            closestMatches = []


        for trueIndex, (dist, predIndex) in enumerate(zip(*closestMatches)) :
            if is_eq(realSegs[trueIndex], predSegs[predIndex]) :
                assocs_Correct.append(predSegs[predIndex])
                # To make sure that I don't compare against that item again.
                del unmatchedPredTrackSegs[unmatchedPredTrackSegs.index(predIndex)]
            else :
                # This segment represents those that were completely
                # missed by the tracking algorithm.
                falarms_Wrong.append(realSegs[trueIndex])

    # Anything left from the predicted segments must be unmatched with reality,
    # therefore, these segments belong in the "assocs_Wrong" array.
    assocs_Wrong = [predSegs[index] for index in unmatchedPredTrackSegs]

    if len(predFAlarmSegs) > 0 :
        predTree = KDTree([(aSeg['xLocs'][0], aSeg['yLocs'][0]) for aSeg in predFAlarmSegs])
        trueData = [(aSeg['xLocs'][0], aSeg['yLocs'][0]) for aSeg in realFAlarmSegs]

        if len(realFAlarmSegs) > 0 :
            closestMatches = predTree.query(trueData)
        else :
            closestMatches = []

        # Now for the falarms...
        for trueIndex, (dist, predIndex) in enumerate(zip(*closestMatches)) :
            if is_eq(realFAlarmSegs[trueIndex], predFAlarmSegs[predIndex]) :		
                falarms_Correct.append(realFAlarmSegs[trueIndex])

        # This FAlarm represents those that may have been falsely associated (assocs_Wrong)...
        # Well... technically, it just means that the tracking algorithm did not declare it
        #         as a false alarm.  Maybe it did not declare it as anything?
        # TODO: Not sure if there is anything I want to do about these for now...
        #       They might already have been accounted for earlier.
#        if not foundMatch :
#            print "<<<< Falsely Associated! ", realFAlarmXLoc, realFAlarmYLoc, realFAlarmFrameNum, " >>>>"

    # Anything left from the predicted non-associations are unmatched with reality.
    # therefore, these segments belong in the "falarms_Wrong" array.
    # NOTE: however, these might have already been accounted for...
#    for index in unmatchedPredFAlarms :
#   print "<<<< Falsely Non-Associated! ", index, predFAlarmSegs['xLocs'][index][0], predFAlarmSegs['yLocs'][index][0], predFAlarmSegs['frameNums'][index][0], " >>>>"
#    print "assocs_Wrong: ", assocs_Wrong
#    print "falarms_Wrong: ", falarms_Wrong
    return {'assocs_Correct': assocs_Correct, 'assocs_Wrong': assocs_Wrong,
            'falarms_Wrong': falarms_Wrong, 'falarms_Correct': falarms_Correct}



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
    allTimes = [volData['volTime'] for volData in volumes]

    return ((allPoints['xLocs'].min(), allPoints['xLocs'].max()),
            (allPoints['yLocs'].min(), allPoints['yLocs'].max()),
            (min(allTimes), max(allTimes)))


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

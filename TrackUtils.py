import math
import numpy
import numpy.lib.recfunctions as nprf		# for .stack_arrays(), .append_fields()
from scipy.spatial import KDTree

corner_dtype = [('xLocs', 'f4'), ('yLocs', 'f4'), ('cornerIDs', 'i4')]
track_dtype = corner_dtype + [('t', 'f4'), ('types', 'a1')]
volume_dtype = track_dtype + [('trackID', 'i4')]
#storm_dtype = track_dtype + [('types', 'a1'), ('t', 'f4'), ('trackID', 'i4')]

# TODO: Maybe use a combination of frameCnt and tLims?
def CreateVolData(tracks, falarms, frameCnt, times, xLims, yLims) :
    """
    Essentially, go from lagrangian (following a particle)
    to eulerian (at fixed points on a grid).

    Note that this method will retain the 'trackID' number,
    so it is possible to reconstruct the (clipped) track data using
    this output.
    """
    volData = []
    tmpTracks = [nprf.append_fields(aTrack, 'trackID',
                                    [trackIndex] * len(aTrack),
                                    usemask=False)
                      for trackIndex, aTrack in enumerate(tracks)]

    # Mark these track indexes as negative (minus one)
    tmpFalarms = [nprf.append_fields(aTrack, 'trackID',
                                     [-trackIndex - 1] * len(aTrack),
                                     usemask=False)
                      for trackIndex, aTrack in enumerate(falarms)]

    if len(tmpTracks) != 0 or len(tmpFalarms) != 0 :
        allCells = numpy.hstack(tmpTracks + tmpFalarms)
    else :
        allCells = numpy.array([], dtype=track_dtype)

    # Note, this is a mask in the opposite sense from a numpy masked array.
    #       True means that this is a value to keep.
    domainMask = numpy.logical_and(allCells['xLocs'] >= min(xLims),
                 numpy.logical_and(allCells['xLocs'] <= max(xLims),
                 numpy.logical_and(allCells['yLocs'] >= min(yLims),
                                   allCells['yLocs'] <= max(yLims))))

    # Find out which frame each storm cell belongs to.
    # Doing a minus one here because of how digitize works
    tIndicies = numpy.digitize(allCells['t'], times) - 1

    for index, volTime in enumerate(times) :
        # Again, this mask is opposite from numpy masked array.
        tMask = (tIndicies == index)
        volData.append({'volTime': volTime,
                        'stormCells': allCells[numpy.logical_and(domainMask, tMask)]})

    return(volData)


def ClipTracks(tracks, falarms, xLims, yLims, tLims) :
    """
    Return a copy of the tracks and falarms, clipped to within
    the given domain.

    All tracks clipped to length of one are moved to a copy of falarms.
    """
    # Note, this is a mask in the opposite sense from a numpy masked array.
    #       Here, True means that this is a value to keep.
    clippedTracks = [ClipTrack(aTrack, xLims, yLims, tLims) for aTrack in tracks]
    clippedFAlarms = [ClipTrack(aTrack, xLims, yLims, tLims) for aTrack in falarms]

    CleanupTracks(clippedTracks, clippedFAlarms)
#    print "Length of tracks outside: ", len(clippedTracks)
    return clippedTracks, clippedFAlarms

def ClipTrack(track, xLims, yLims, tLims) :
    domainMask = numpy.logical_and(track['xLocs'] >= min(xLims),
                 numpy.logical_and(track['xLocs'] <= max(xLims),
                 numpy.logical_and(track['yLocs'] >= min(yLims),
                 numpy.logical_and(track['yLocs'] <= max(yLims),
                 numpy.logical_and(track['t'] >= min(tLims),
                                   track['t'] <= max(tLims))))))

    return track[domainMask]

def FilterTrack(track, frames) :
    mask = numpy.array([(aFrame['t'] in frames) for aFrame in track], dtype=bool)
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
            segs.extend([numpy.hstack(aSeg) for aSeg in zip(aTrack[0:trackLen - 1],
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

        closestMatches = predTree.query(trueData)

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

        closestMatches = predTree.query(trueData)
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
#	print "<<<< Falsely Non-Associated! ", index, predFAlarmSegs['xLocs'][index][0], predFAlarmSegs['yLocs'][index][0], predFAlarmSegs['frameNums'][index][0], " >>>>"
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


def DomainFromTracks(tracks, falarms = []) :
    """
    Calculate the spatial and temporal domain of the tracks and false alarms.
    Note that this assumes that bad points are non-existant or has been
    masked out.
    """

    allPoints = numpy.hstack(tracks + falarms)
    
    return ((allPoints['xLocs'].min(), allPoints['xLocs'].max()),
            (allPoints['yLocs'].min(), allPoints['yLocs'].max()),
            (allPoints['t'].min(), allPoints['t'].max()))

def DomainFromVolumes(volumes) :
    """
    Calculate the spatial and temporal domain of the volume data.
    Assumes that bad points are non-existant or has been masked out.

    Note that this is slightly different from DomainFromTracks because
    stormcells in a volume array do not have time info.
    """
    allPoints = numpy.hstack([volData['stormCells'] for volData in volumes])
    allTimes = [volData['volTime'] for volData in volumes]

    return ((allPoints['xLocs'].min(), allPoints['xLocs'].max()),
            (allPoints['yLocs'].min(), allPoints['yLocs'].max()),
            (min(allTimes), max(allTimes)))


def is_eq(seg1, seg2) :
    """
    Use the cornerIDs of the segments to evaluate equality.
    """
    return numpy.all(seg1['cornerIDs'] == seg2['cornerIDs'])

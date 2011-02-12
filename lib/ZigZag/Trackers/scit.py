import math                                 # for abs(), sqrt()
import numpy
import numpy.lib.recfunctions as nprf       # for append_fields()
from ZigZag.TrackUtils import volume_dtype



# This code serves to duplicate how SCIT does its tracking for testing purposes

# Place some startup stuff here, maybe?

def TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, volume_Data) :
# strmHist is a vector containing info for what happened at each time-step
# volume_Data contains the current volume's storm cells
# strmAdap parameterizes the algorithm

    strmCnt = len(volume_Data['stormCells'])
    # The volume data has only xLocs and yLocs,
    # so we need to add some track-relevant fields
    # to the data without modifying the input data.
    currStrms = nprf.append_fields(volume_Data['stormCells'],
                                   ('frameNums', 'types', 'trackID'),
                                   ([volume_Data['frameNum']] * strmCnt,
                                    ['F'] * strmCnt,
                                    [-1] * strmCnt),
                                   usemask=False)
 
    BestLocs(stateHist, infoTracks, volume_Data['frameNum'])
    Correl_Storms(strmAdap, currStrms, volume_Data['frameNum'], stateHist, strmTracks, infoTracks)
    Compute_Speed(currStrms, strmTracks, infoTracks)
    EndTracks(stateHist, strmTracks, currStrms)


    stateHist.append({'volTime': volume_Data['frameNum'],
                      'stormCells': currStrms})

def EndTracks(stateHist, strmTracks, currStrms=None) :
    """
    After the storm cells have been associated with tracks, now we need to
    determine which tracks have to be 'turned off' and clean up the data in
    the track data.

    Call this function without a currStrms argument when you are finished tracking and
    want to finalize the tracks.
    """
    if len(stateHist) == 0 :
        # Ah, there is no history, therefore, there are no established tracks
        return

    # build list of track ids for the stormcells in the previous frame
    prevTracks = set([aCell['trackID'] for aCell in stateHist[-1]['stormCells']])

    if currStrms is not None :
        currTracks = set(currStrms['trackID'])
    else :
        currTracks = set([])


    # Find the set difference of the list of tracks.
    # The difference would be whatever tracks that existed in the previous
    # frame, but not in the current frame.
    unmatchedTrackIDs = prevTracks - currTracks

    # Now end those tracks
    #    - Any tracks that are of length 2 or longer have
    #          their last storm cell marked as 'M' because
    #          it belonged to a track.
    #  Maybe some other tasks?
    for aTrackID in unmatchedTrackIDs :
        if len(strmTracks[aTrackID]) > 1 :
            # Mark the last storm cell in the track as "matched"
            strmTracks[aTrackID]['types'][-1] = 'M'


def Correl_Storms(strmAdap, currStorms, volTime, stateHist, strmTracks, infoTracks) :
    prevStorms = ()
    if (len(stateHist) != 0) :
        prevStorms = stateHist[-1]['stormCells']

    # Looping over the current storms to compare against the previous storms
    for newCell in currStorms :
        bestMatch = {'prevIndx': None, 
                     'dist': strmAdap['distThresh']**2}

        for oldIndex, oldStorm in enumerate(prevStorms) :
            
            # not equal to 'M' means that storm hasn't been matched yet.
            if oldStorm['types'] != 'M' :

                # Grab the forecasted location for the current point,
                # which can be found in its track's 'fcasts' element.
                cellDist = CalcDistSqrd(newCell,
                                        infoTracks[oldStorm['trackID']]['fcasts'][-1])
                if cellDist < bestMatch['dist'] :
                    bestMatch = {'prevIndx': oldIndex, 'dist': cellDist}


        if bestMatch['prevIndx'] is not None :
            # Note how it goes ahead and matches with the first storm cell it finds
            # that is below the threshold.  I believe this to be a bug that can cause
            # "track-stealing" as the algorithm does not find the closest stormcell,
            # only the first one that was "close enough".
            # In other words, while this oldCell is the closest oldCell to this newCell,
            # it doesn't necessarially mean that this newCell is the closest newCell to
            # this oldCell.
            # This is *partly* mitigated by sorting the storm cells by size.  Larger
            # storm cells have more stable centroids (less noisey).  Track stealing
            # more likely to occur with noisey cell centroids.
            # However, note that any sort of sorting must be done outside of the SCIT tracking functions.
            # In other words, the passed-in storm cells should have already been sorted.

            matchedStorm = prevStorms[bestMatch['prevIndx']]

           
            # Assigning the current storm its track ID number
            trackID = newCell['trackID'] = matchedStorm['trackID']

            # Indicate that the storm in the previous frame has
            # now been matched.
            strmTracks[trackID]['types'][-1] = 'M'
    
            infoTracks[trackID]['distErrs'].append(math.sqrt(bestMatch['dist']))
            infoTracks[trackID]['dists'].append(math.sqrt(CalcDistSqrd(newCell, matchedStorm)))
            # Adding a new point to the established storm track
            strmTracks[trackID] = numpy.hstack((strmTracks[trackID], newCell))

        else :
            # We did not find a suitable match, so we create a new track.
            # Give it the next available ID number.
            newCell['trackID'] = len(strmTracks)
            infoTracks.append({'distErrs': [0.0],
                               'dists': [0.0],
                               'fcasts': [],
                               'speed_x': [],
                               'speed_y': []})
            strmTracks.append(numpy.array([newCell], dtype=volume_dtype))


def CalcDistSqrd(cellA, cellB) :
    return( (cellA['xLocs'] - cellB['xLocs'])**2 +
            (cellA['yLocs'] - cellB['yLocs'])**2 )


def BestLocs(stateHist, infoTracks, volTime) :
    """
    Forecast where the active tracks will go.
    """
    # Need to do a forecast if the history is empty
    if len(stateHist) > 0 :
        deltaTime = volTime - stateHist[-1]['volTime']

        for stormCell in stateHist[-1]['stormCells'] :
            #print "BestLocs:", stormCell
            theTrack = infoTracks[stormCell['trackID']]
            #stormCell['corFlag'] = False
            theTrack['fcasts'].append({'xLocs': stormCell['xLocs'] + (theTrack['speed_x'][-1] * deltaTime),
                                       'yLocs': stormCell['yLocs'] + (theTrack['speed_y'][-1] * deltaTime)})



def Compute_Speed(currStorms, strmTracks, infoTracks) :
    """
    Updates the speed for all of the current, active tracks.
    Also initiates all new tracks with the average speed of all
    of the other active tracks.
    """
    tot_x_spd = 0.0
    tot_y_spd = 0.0
    trackCnt = 0

    # Gonna first calculate the track speed for all established tracks
    # in order to determine an overall average speed to use for initializing
    # the speed for un-established tracks.
    for stormCell in currStorms :
        #print "CurrStorm..."

        theTrackInfo = infoTracks[stormCell['trackID']]
        aTrack = strmTracks[stormCell['trackID']]
        #trackLen = len(theTrackInfo['track'])

        if len(aTrack) > 1 :
            xAvg = numpy.mean(aTrack['xLocs'][-10:])
            yAvg = numpy.mean(aTrack['yLocs'][-10:])
            tAvg = numpy.mean(aTrack['frameNums'][-10:])

            #xtVar = sum([(xLoc - xAvg) * (trackTime - tAvg)
            #	         for (xLoc, trackTime) in zip(aTrack['xLocs'], aTrack['frameNums'])])
            #ytVar = sum([(yLoc - yAvg) * (trackTime - tAvg)
            #	         for (yLoc, trackTime) in zip(aTrack['yLocs'], aTrack['frameNums'])])
            #ttVar = sum([(trackTime - tAvg)**2
            #	         for trackTime in aTrack['frameNums']])

            tDev = aTrack['frameNums'][-10:] - tAvg
            xtVar = numpy.sum((aTrack['xLocs'][-10:] - xAvg) * tDev)
            ytVar = numpy.sum((aTrack['yLocs'][-10:] - yAvg) * tDev)
            ttVar = numpy.sum(tDev**2)

            tot_x_spd += (xtVar / ttVar)
            tot_y_spd += (ytVar / ttVar)
            trackCnt += 1

            theTrackInfo['speed_x'].append(xtVar / ttVar)
            theTrackInfo['speed_y'].append(ytVar / ttVar)


    if (trackCnt != 0) :
        systemAvg = {'speed_x': tot_x_spd / trackCnt,
                     'speed_y': tot_y_spd / trackCnt}
    else :
        systemAvg = {'speed_x': 0.0,
                     'speed_y': 0.0}

    # Now initialize any unestablished tracks with the sytem average
    for stormCell in currStorms :
        theTrackInfo = infoTracks[stormCell['trackID']]
        if len(theTrackInfo['speed_x']) == 0 :
            theTrackInfo['speed_x'].append(systemAvg['speed_x'])
            theTrackInfo['speed_y'].append(systemAvg['speed_y'])


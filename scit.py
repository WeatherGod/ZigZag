import math	# for abs(), sqrt()
import numpy
import numpy.lib.recfunctions as nprf		# for append_fields()


corner_dtype = [('xLocs', 'f4'), ('yLocs', 'f4')]
storm_dtype = corner_dtype + [('types', 'a1'), ('frameNums', 'i4'), ('trackID', 'i4')]

# This code serves to duplicate how SCIT does its tracking for testing purposes

# Place some startup stuff here, maybe?

def TrackStep_SCIT(strmAdap, stateHist, strmTracks, volume_Data) :
# strmHist 	is a vector containing info for what happened at each time-step
# volume_Data 	contains the current volume's storm cells
# strmAdap 	parameterizes the algorithm
    strmCnt = len(volume_Data['stormCells'])
    currStrms = nprf.append_fields(volume_Data['stormCells'],
                                   ('types', 'frameNums', 'trackID'),
                                   (['F'] * strmCnt,
                                    [volume_Data['volTime']] * strmCnt,
                                    [-1] * strmCnt),
                                   usemask=False)
 
    BestLocs(stateHist, strmTracks, volume_Data['volTime'])
    Correl_Storms(strmAdap, currStrms, volume_Data['volTime'], stateHist, strmTracks)
    Compute_Speed(currStrms, strmTracks)


    stateHist.append({'volTime': volume_Data['volTime'],
                      'stormCells': currStrms})



def Correl_Storms(strmAdap, currStorms, volTime, stateHist, strmTracks) :
    prevStorms = ()
    if (len(stateHist) != 0) :
        prevStorms = stateHist[-1]['stormCells']

    # Looping over the current storms to compare against the previous storms
    for newCell in currStorms :
	bestMatch = {'prevIndx': None, 
		     'dist': strmAdap['distThresh']**2}

        for oldIndex in xrange(len(prevStorms)) :
            # not equal to 'M' means that storm hasn't been matched yet.
	    if prevStorms['types'][oldIndex] != 'M' :
                # Grab the forecasted location for the current point,
                # which can be found in its track's 'fcasts' element.
		cellDist = CalcDistSqrd(newCell,
                                        strmTracks[prevStorms[oldIndex]['trackID']]['fcasts'][-1])
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
            # Indicate that it has now been matched.
	    matchedStorm['types'] = 'M'

            # Assigning the current storm its track ID number
	    newCell['trackID'] = matchedStorm['trackID']

	    matchedTrack = strmTracks[newCell['trackID']]
	    matchedTrack['distErrs'].append(math.sqrt(bestMatch['dist']))
	    matchedTrack['dists'].append(math.sqrt(CalcDistSqrd(newCell, matchedStorm)))
	    matchedTrack['track'] = numpy.hstack((matchedTrack['track'], newCell))

	else :
            # We did not find a suitable match, so we create a new track.
            # Give it the next available ID number.
            #print "New Track!", newCell
	    newCell['trackID'] = len(strmTracks)
	    strmTracks.append({'distErrs': [0.0],
			       'dists': [0.0],
                               'track': numpy.array([newCell], dtype=storm_dtype),
                               'fcasts': [],
                               'speed_x': [],
                               'speed_y': []
				})


def CalcDistSqrd(cellA, cellB) :
    return( (cellA['xLocs'] - cellB['xLocs'])**2 +
            (cellA['yLocs'] - cellB['yLocs'])**2 )


def BestLocs(stateHist, strmTracks, volTime) :
    """
    Forecast where the active tracks will go.
    """
    # Need to do a forecast if the history is empty
    if len(stateHist) > 0 :
        deltaTime = volTime - stateHist[-1]['volTime']

        for stormCell in stateHist[-1]['stormCells'] :
            #print "BestLocs:", stormCell
            theTrack = strmTracks[stormCell['trackID']]
            #stormCell['corFlag'] = False
	    theTrack['fcasts'].append({'xLocs': stormCell['xLocs'] + (theTrack['speed_x'][-1] * deltaTime),
			               'yLocs': stormCell['yLocs'] + (theTrack['speed_y'][-1] * deltaTime)})



def Compute_Speed(currStorms, strmTracks) :
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
	
	theTrackInfo = strmTracks[stormCell['trackID']]
        aTrack = theTrackInfo['track']
	#trackLen = len(theTrackInfo['track'])

	if len(theTrackInfo['track']) > 1 :
            xAvg = numpy.mean(aTrack['xLocs'])
            yAvg = numpy.mean(aTrack['yLocs'])
            tAvg = numpy.mean(aTrack['frameNums'])

	    #xtVar = sum([(xLoc - xAvg) * (trackTime - tAvg)
	    #	         for (xLoc, trackTime) in zip(aTrack['xLocs'], aTrack['frameNums'])])
	    #ytVar = sum([(yLoc - yAvg) * (trackTime - tAvg)
	    #	         for (yLoc, trackTime) in zip(aTrack['yLocs'], aTrack['frameNums'])])
	    #ttVar = sum([(trackTime - tAvg)**2
	    #	         for trackTime in aTrack['frameNums']])

            tDev = aTrack['frameNums'] - tAvg
            xtVar = numpy.sum((aTrack['xLocs'] - xAvg) * tDev)
            ytVar = numpy.sum((aTrack['yLocs'] - yAvg) * tDev)
            ttVar = numpy.sum(tDev**2)

	    tot_x_spd += (xtVar / ttVar)
	    tot_y_spd += (ytVar / ttVar)
            trackCnt += 1

	    theTrackInfo['speed_x'].append(xtVar / ttVar)
            theTrackInfo['speed_y'].append(ytVar / ttVar)


    if (trackCnt != 0) :
        systemAvg = {'speed_x': tot_x_spd / trackCnt, 'speed_y': tot_y_spd / trackCnt}
    else :
        systemAvg = {'speed_x': 0.0, 'speed_y': 0.0}


    for stormCell in currStorms :
        theTrackInfo = strmTracks[stormCell['trackID']]
	if len(theTrackInfo['track']) == 1 :
	    theTrackInfo['speed_x'].append(systemAvg['speed_x'])
            theTrackInfo['speed_y'].append(systemAvg['speed_y'])


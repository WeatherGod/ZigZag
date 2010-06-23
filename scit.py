import math	# for abs(), sqrt()
import numpy
import numpy.lib.recfunctions as nprf		# for append_fields()

# This code serves to duplicate how SCIT does its tracking for testing purposes

# Place some startup stuff here, maybe?

def TrackStep_SCIT(strmAdap, stateHist, strmTracks, volume_Data) :
# strmHist 	is a vector containing info for what happened at each time-step
# volume_Data 	contains the current volume's storm cells
# strmAdap 	parameterizes the algorithm

    currStrms = nprf.append_fields(volume_Data['stormCells'], ('trackID', 'corFlag'),
                                   ([-1] * len(volume_Data['stormCells']),
                                    [False] * len(volume_Data['stormCells'])),
                                   usemask=False)
 
    BestLocs(stateHist, volume_Data['volTime'])
    Correl_Storms(strmAdap, currStrms, volume_Data['volTime'], stateHist, strmTracks)
    Compute_Speed(currStrms, strmTracks)


    stateHist.append(volume_Data)



def Correl_Storms(strmAdap, currStorms, volTime, stateHist, strmTracks) :
    prevStorms = []
    if (len(stateHist) != 0) :
        prevStorms = stateHist[-1]['stormCells']


    for newCell in currStorms :
	bestMatch = {'prevIndx': None, 
		     'dist': strmAdap['distThresh']**2}

        for oldIndex in xrange(len(prevStorms)) :
	    if (not prevStorms[oldIndex]['corFlag']) :
		cellDist = CalcDistSqrd(newCell, prevStorms[oldIndex].fcast)
		if (cellDist < bestMatch['dist']) :
                    bestMatch = {'prevIndx': oldIndex, 'dist': cellDist}


	if (bestMatch['prevIndx'] is not None) :
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
	    matchedStorm['corFlag'] = True

	    newCell['trackIndx'] = matchedStorm['trackIndx']

	    matchedTrack = strmTracks[newCell['trackIndx']]
	    matchedTrack['distErr'].append(math.sqrt(bestMatch['dist']))
	    matchedTrack['dist'].append(math.sqrt(CalcDistSqrd(newCell, matchedStorm)))
	    matchedTrack['xLocs'].append(newCell['xLoc'])
	    matchedTrack['yLocs'].append(newCell['yLoc'])
	    matchedTrack['frameNums'].append(matchedTrack['frameNums'][-1] 
					     + matchedStorm.fcast['deltaTime'])
	else :
	    newCell['trackIndx'] = len(strmTracks)
	    strmTracks.append({'distErr': [0.0], 
				 'dist': [0.0], 
				 'xLocs': [newCell['xLoc']],
				 'yLocs': [newCell['yLoc']],
				 'frameNums': [volTime]} )



def CalcDistSqrd(cellA, cellB) :
    return( (cellA['xLoc'] - cellB['xLoc'])**2 + (cellA['yLoc'] - cellB['yLoc'])**2 )


def BestLocs(stateHist, volTime) :
    
    if (len(stateHist) > 0) :
        deltaTime = volTime - stateHist[-1]['volTime']

        for stormCell in stateHist[-1]['stormCells'] :
            stormCell['corFlag'] = False
	    stormCell.fcast = {'xLoc': stormCell['xLoc'] + (stormCell['speed_x'] * deltaTime),
			       'yLoc': stormCell['yLoc'] + (stormCell['speed_y'] * deltaTime),
			       'deltaTime': deltaTime}



def Compute_Speed(currStorms, strmTracks) :
    """
    Updates the speed for all of the current, active tracks.
    Also initiates all new tracks with the average speed of all
    of the other active tracks.
    """
    tot_x_spd = 0.0
    tot_y_spd = 0.0
    trackCnt = 0

    for stormCell in currStorms :
	
	aTrack = strmTracks[stormCell['trackIndx']]
	trackLen = len(aTrack['frameNums'])

	if (trackLen > 1) :
            xAvg = sum(aTrack['xLocs']) / trackLen
            yAvg = sum(aTrack['yLocs']) / trackLen
            tAvg = sum(aTrack['frameNums']) / trackLen

	    xtVar = sum([(xLoc - xAvg) * (trackTime - tAvg)
		         for (xLoc, trackTime) in zip(aTrack['xLocs'], aTrack['frameNums'])])
	    ytVar = sum([(yLoc - yAvg) * (trackTime - tAvg)
		         for (yLoc, trackTime) in zip(aTrack['yLocs'], aTrack['frameNums'])])
	    ttVar = sum([(trackTime - tAvg)**2
		         for trackTime in aTrack['frameNums']])

	    tot_x_spd += (xtVar / ttVar)
	    tot_y_spd += (ytVar / ttVar)
            trackCnt += 1

	    stormCell.update({'speed_x': xtVar / ttVar, 'speed_y': ytVar / ttVar})

    systemAvg = {'speed_x': 0.0, 'speed_y': 0.0}
    if (trackCnt != 0) :
        systemAvg = {'speed_x': tot_x_spd / trackCnt, 'speed_y': tot_y_spd / trackCnt}


    for stormCell in currStorms :
	if (len(strmTracks[stormCell['trackIndx']]['frameNums']) == 1) :
	    stormCell['speed_x'] = systemAvg['speed_x']
            stormCell['speed_y'] = systemAvg['speed_y']


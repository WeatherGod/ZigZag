import math	# for abs(), sqrt()

# This code serves to duplicate how SCIT does its tracking for testing purposes

# Place some startup stuff here, maybe?

def TrackStep_SCIT(strmAdap, stateHist, strmTracks, volume_Data) :
# strmHist 	is a vector containing info for what happened at each time-step
# volume_Data 	contains the current volume's storm cells
# strmAdap 	parameterizes the algorithm
 
    BestLocs(stateHist, volume_Data['volTime'])
    Correl_Storms(strmAdap, volume_Data['stormCells'], stateHist, strmTracks)
    Compute_Speed(volume_Data['stormCells'], strmTracks)


    stateHist.append(volume_Data)



def Correl_Storms(strmAdap, currStorms, stateHist, strmTracks) :
    prevStorms = []
    if (len(stateHist) != 0) :
        prevStorms = stateHist[-1]['stormCells']


    for newCell in currStorms :
	bestMatch = {'prevIndx': None, 
		     'dist': strmAdap['distThresh']**2}

        for oldIndex in range(len(prevStorms)) :
	    if (not prevStorms[oldIndex]['corFlag']) :
		cellDist = CalcDistSqrd(newCell, prevStorms[oldIndex]['fcast'])
		if (cellDist < bestMatch['dist']) :
                    bestMatch = {'prevIndx': oldIndex, 'dist': cellDist}


	if (bestMatch['prevIndx'] != None) :
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

	    matchedStorm = prevStorms[bestMatch['prevIndx']]
	    matchedStorm['corFlag'] = True
	    newCell.update({'trackIndx': matchedStorm['trackIndx']})
	    strmTracks[newCell['trackIndx']].append({'distErr': math.sqrt(bestMatch['dist']),
						     'dist': math.sqrt(CalcDistSqrd(newCell, matchedStorm)),
						     'strmCell': newCell, 
						     'trackTime': strmTracks[newCell['trackIndx']][-1]['trackTime'] 
								  + matchedStorm['fcast']['deltaTime']})
	else :
	    newCell.update({'trackIndx': len(strmTracks)})
	    strmTracks.append([ {'distErr': 0.0, 
				 'dist': 0.0, 
				 'strmCell': newCell, 
				 'trackTime': 0} ])



def CalcDistSqrd(cellA, cellB) :
    return( (cellA['xLoc'] - cellB['xLoc'])**2 + (cellA['yLoc'] - cellB['yLoc'])**2 )


def BestLocs(stateHist, volTime) :
    
    if (len(stateHist) > 0) :
        deltaTime = volTime - stateHist[-1]['volTime']

        for stormCell in stateHist[-1]['stormCells'] :
	    stormCell.update({'corFlag': False, 
	    		      'fcast': {'xLoc': stormCell['xLoc'] + (stormCell['speed_x'] * deltaTime),
			                'yLoc': stormCell['yLoc'] + (stormCell['speed_y'] * deltaTime),
			                'deltaTime': deltaTime}})



def Compute_Speed(currStorms, strmTracks) :
    tot_x_spd = 0.0
    tot_y_spd = 0.0
    trackCnt = 0

    for stormCell in currStorms :
	
	trackIndex = stormCell['trackIndx']
	trackLen = len(strmTracks[trackIndex])

	if (trackLen > 1) :
            xAvg = sum([trackCell['strmCell']['xLoc'] for trackCell in strmTracks[trackIndex]]) / trackLen
            yAvg = sum([trackCell['strmCell']['yLoc'] for trackCell in strmTracks[trackIndex]]) / trackLen
            tAvg = strmTracks[trackIndex][-1]['trackTime'] / trackLen

	    xtVar = sum([(trackCell['strmCell']['xLoc'] - xAvg)
		         * (trackCell['trackTime'] - tAvg)
		         for trackCell in strmTracks[trackIndex]])
	    ytVar = sum([(trackCell['strmCell']['yLoc'] - yAvg)
		         * (trackCell['trackTime'] - tAvg)
		         for trackCell in strmTracks[trackIndex]])
	    ttVar = sum([(trackCell['trackTime'] - tAvg)**2
		         for trackCell in strmTracks[trackIndex]])

	    tot_x_spd += (xtVar / ttVar)
	    tot_y_spd += (ytVar / ttVar)
            trackCnt += 1

	    stormCell.update({'speed_x': xtVar / ttVar, 'speed_y': ytVar / ttVar})

    systemAvg = {'speed_x': 0.0, 'speed_y': 0.0}
    if (trackCnt != 0) :
        systemAvg = {'speed_x': tot_x_spd / trackCnt, 'speed_y': tot_y_spd / trackCnt}


    for stormCell in currStorms :
	if (len(strmTracks[stormCell['trackIndx']]) == 1) :
	    stormCell.update(systemAvg)


import math
import copy                             # for deep copying


def CreateVolData(tracks, falarms, tLims, xLims, yLims) :
    """
    Essentially, go from lagrangian (following a particle)
    to eulerian (at fixed points on a grid).

    Note that this method will retain the 'trackID' number,
    so it is possible to reconstruct the (clipped) track data using
    this output.
    """
    volData = []
    allCells = {'frameNums': [], 'trackID': [], 'xLocs': [], 'yLocs': []}
    #print "Tracks:"
    for aTrack in tracks :
	#print aTrack['trackID'], '\t', aTrack['frameNums']
	#print "THIS TRACK:   ", aTrack
        allCells['frameNums'].extend(aTrack['frameNums'])
        allCells['trackID'].extend([aTrack['trackID']] * len(aTrack['frameNums']))
        allCells['xLocs'].extend(aTrack['xLocs'])
        allCells['yLocs'].extend(aTrack['yLocs'])

    #print "\n\nFAlarms"
    for aFAlarm in falarms :
	#print aFAlarm['trackID'], '\t', aFAlarm['frameNums']
	#print "THIS FALARM: ", aFAlarm
	allCells['frameNums'].extend(aFAlarm['frameNums'])
	allCells['trackID'].extend([aFAlarm['trackID']] * len(aFAlarm['frameNums']))
	allCells['xLocs'].extend(aFAlarm['xLocs'])
	allCells['yLocs'].extend(aFAlarm['yLocs'])



    for volTime in range(min(tLims), max(tLims) + 1) :
        volData.append({'volTime': volTime,
                        'stormCells': [{'xLoc': xLoc, 'yLoc': yLoc, 'trackID': trackID}
                                       for (xLoc, yLoc, frameNum, trackID) in zip(allCells['xLocs'], allCells['yLocs'], allCells['frameNums'], allCells['trackID'])
                                        if (frameNum == volTime and xLoc >= min(xLims) and xLoc <= max(xLims) and
                                                                    yLoc >= min(yLims) and yLoc <= max(yLims))]})

    return(volData)


def ClipTracks(tracks, falarms, xLims, yLims, tLims) :
    """
    Return a copy of the tracks and falarms, clipped to within
    the given domain.

    All tracks clipped to length of one are moved to a copy of falarms.
    """
    clippedTracks = copy.deepcopy(tracks)
    clippedFAlarms = copy.deepcopy(falarms)
    for aTrack in clippedTracks :
        for (index, (xLoc, yLoc, frameNum)) in enumerate(zip(aTrack['xLocs'], aTrack['yLocs'], aTrack['frameNums'])) :
            if (xLoc < min(xLims) or xLoc > max(xLims) or
                yLoc < min(yLims) or yLoc > max(yLims) or
                frameNum < min(tLims) or frameNum > max(tLims)) :
                # Flag this track as one to get rid of.
                for aKey in aTrack : 
		    if aKey != 'trackID' : aTrack[aKey][index] = None



    (clippedTracks, clippedFAlarms) = CleanupTracks(clippedTracks, clippedFAlarms)
#    print "Length of tracks outside: ", len(clippedTracks)
    return (clippedTracks, clippedFAlarms)


def CleanupTracks(tracks, falarms) :
    """
    Rebuild the track list, effectively removing the storms flagged by a 'None'
    Also handles tracks that were shortened or effectively removed to the
    falarms list.
    """
    # This will indicate how much to change the trackID
    # number for each track as tracks are removed.
    # This allows for other code to use the trackID number
    # associated with a strmCell
    # as a list index into the track list.
    modifyTrackID = 0
    for trackID in range(len(tracks)) :
        for aKey in tracks[trackID] : 
	    if aKey != "trackID" : tracks[trackID][aKey] = [someVal for someVal in tracks[trackID][aKey] if someVal is not None]
	    else : tracks[trackID][aKey] -= modifyTrackID
	
	# move any length-1 tracks to the falarms category
	if len(tracks[trackID]['frameNums']) == 1 :
	    tracks[trackID]['trackID'] = -1
	    falarms.append(tracks[trackID].copy())
	    for aKey in tracks[trackID] : 
		if aKey != "trackID" : tracks[trackID][aKey] = []
        
	# completely remove any length-0 tracks
	#  (or the tracks that were moved to falarms)
	if len(tracks[trackID]['frameNums']) == 0 :
	    modifyTrackID += 1
	    # Flag for removal.
	    tracks[trackID] = None
        

    # Rebuild track list
    tracks = [aTrack for aTrack in tracks if aTrack is not None]
#    print "Length of tracks: ", len(tracks)
    return(tracks, falarms)




def CreateSegments(tracks) :
    """
    Breaks up a list of the tracks (or falarms) into an array of segments.
    Each element in the arrays represents the start and end point of a segment.
    """

    xLocs = []
    yLocs = []
    frameNums = []
    for aTrack in tracks :
        if len(aTrack['frameNums']) > 1 :
            for index2 in range(1, len(aTrack['frameNums'])) :
                index1 = index2 - 1
                xLocs.append([aTrack['xLocs'][index1], aTrack['xLocs'][index2]])
                yLocs.append([aTrack['yLocs'][index1], aTrack['yLocs'][index2]])
                frameNums.append([aTrack['frameNums'][index1], aTrack['frameNums'][index2]])
	else :
	    xLocs.append(aTrack['xLocs'])
	    yLocs.append(aTrack['yLocs'])
	    frameNums.append(aTrack['frameNums'])


    return {'xLocs': xLocs, 'yLocs': yLocs, 'frameNums': frameNums}


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
""" % (len(truthTable['assocs_Correct']['xLocs']), len(truthTable['assocs_Wrong']['xLocs']),
       len(truthTable['falarms_Wrong']['xLocs']), len(truthTable['falarms_Correct']['xLocs']))


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
    assocs_Correct = {'xLocs': [], 'yLocs': [], 'frameNums': []}
    falarms_Correct = {'xLocs': [], 'yLocs': [], 'frameNums': []}
    assocs_Wrong = {'xLocs': [], 'yLocs': [], 'frameNums': []}
    falarms_Wrong = {'xLocs': [], 'yLocs': [], 'frameNums': []}

    seekX = 246.0
    seekY = 63.0

    unmatchedPredTrackSegs = range(len(predSegs['xLocs']))

    for (realSegXLoc, realSegYLoc, realSegFrameNum) in zip(realSegs['xLocs'], 
							   realSegs['yLocs'], 
							   realSegs['frameNums']) :
	foundMatch = False
	for predIndex in unmatchedPredTrackSegs :
	    """
	    if ((seekX <= realSegXLoc[0] <= 247.0) and (seekY <= realSegYLoc[1] <= seekY + 1.)
		and (seekX <= predSegs['xLocs'][predIndex][0] <= seekX + 1.)
		and (seekY <= predSegs['yLocs'][predIndex][0] <= seekY + 1.)) :
		print "Real XLocs: ", realSegXLoc
		print "Pred XLocs: ", predSegs['xLocs'][predIndex]
		print "Real YLocs: ", realSegYLoc
		print "Pred YLocs: ", predSegs['yLocs'][predIndex]
	    """
		
	    if (is_eq(realSegXLoc[0], predSegs['xLocs'][predIndex][0]) and
	        is_eq(realSegXLoc[1], predSegs['xLocs'][predIndex][1]) and
	        is_eq(realSegYLoc[0], predSegs['yLocs'][predIndex][0]) and
	        is_eq(realSegYLoc[1], predSegs['yLocs'][predIndex][1]) and
	        realSegFrameNum[0] == predSegs['frameNums'][predIndex][0] and
	        realSegFrameNum[1] == predSegs['frameNums'][predIndex][1]) :


		assocs_Correct['xLocs'].append(predSegs['xLocs'][predIndex])
		assocs_Correct['yLocs'].append(predSegs['yLocs'][predIndex])
		assocs_Correct['frameNums'].append(predSegs['frameNums'][predIndex])
		# To make sure that I don't compare against that item again.
		del unmatchedPredTrackSegs[unmatchedPredTrackSegs.index(predIndex)]
		foundMatch = True
		# Break out of this loop...
		break

	# This segment represents those that were completely
        # missed by the tracking algorithm.
	if not foundMatch : 
	    falarms_Wrong['xLocs'].append(realSegXLoc)
	    falarms_Wrong['yLocs'].append(realSegYLoc)
	    falarms_Wrong['frameNums'].append(realSegFrameNum)

    # Anything left from the predicted segments must be unmatched with reality,
    # therefore, these segments belong in the "assocs_Wrong" array.
    for index in unmatchedPredTrackSegs :
        #print predSegs['xLocs'][index], predSegs['frameNums'][index]
        assocs_Wrong['xLocs'].append(predSegs['xLocs'][index])
        assocs_Wrong['yLocs'].append(predSegs['yLocs'][index])
        assocs_Wrong['frameNums'].append(predSegs['frameNums'][index])


    # Now for the falarms...
    """
    print "PredFAlarmSegs: "
    for predFAlarm in zip(predFAlarmSegs['xLocs'],
						  predFAlarmSegs['yLocs'],
						  predFAlarmSegs['frameNums']) :
	print predFAlarm
    """
    unmatchedPredFAlarms = range(len(predFAlarmSegs['xLocs']))
    for (realFAlarmXLoc, realFAlarmYLoc, realFAlarmFrameNum) in zip(realFAlarmSegs['xLocs'],
					                            realFAlarmSegs['yLocs'],
					                            realFAlarmSegs['frameNums']):
	foundMatch = False
	for predIndex in unmatchedPredFAlarms :
	    """
	    if ((seekX <= realFAlarmXLoc[0] <= seekX + 1.) and (seekY <= realFAlarmYLoc[0] <= seekY + 1.)
		and (seekX <= predFAlarmSegs['xLocs'][predIndex][0] <= seekX + 1.)
		and (seekY <= predFAlarmSegs['yLocs'][predIndex][0] <= seekY + 1.)) :
		print "Real XLocs: ", realFAlarmXLoc
		print "Pred XLocs: ", predFAlarmSegs['xLocs'][predIndex]
		print "Real YLocs: ", realFAlarmYLoc
		print "Pred YLocs: ", predFAlarmSegs['yLocs'][predIndex]
		print "Real Frame: ", realFAlarmFrameNum, "   Pred Frame: ", predFAlarmSegs['frameNums'][predIndex]
	    """
	    if (is_eq(realFAlarmXLoc[0], predFAlarmSegs['xLocs'][predIndex][0]) and
		is_eq(realFAlarmYLoc[0], predFAlarmSegs['yLocs'][predIndex][0]) and
		realFAlarmFrameNum[0] == predFAlarmSegs['frameNums'][predIndex][0]) :
		
		falarms_Correct['xLocs'].append(realFAlarmXLoc)
		falarms_Correct['yLocs'].append(realFAlarmYLoc)
		falarms_Correct['frameNums'].append(realFAlarmFrameNum)
		# To make sure that I don't compare against that item again.
		del unmatchedPredFAlarms[unmatchedPredFAlarms.index(predIndex)]
                #print "Deleting: ", predIndex
		foundMatch = True
		# Break out of this loop
		break

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


def CalcHeidkeSkillScore(truthTable) :
    """
    Skill score formula from 
	http://www.eumetcal.org.uk/eumetcal/verification/www/english/msg/ver_categ_forec/uos3/uos3_ko1.htm

    HSS = 2(ad - bc) / [(a + c)(c + d) + (a + b)(b + d)]

    Note that a forecast is good when it is closer to 1, and
    is worse if less than zero.

                Observed
              True    False
Forecasted
    True       a        b
    False      c        d
    """

    a = float(len(truthTable['assocs_Correct']['xLocs']))
    b = float(len(truthTable['assocs_Wrong']['xLocs']))
    c = float(len(truthTable['falarms_Wrong']['xLocs']))
    d = float(len(truthTable['falarms_Correct']['xLocs']))
    if (((a + c) * (c + d)) + ((a + b) * (b + d))) < 0.1 :
       return 1.0
    else :
       return 2. * ((a * d) - (b * c)) / (((a + c) * (c + d)) + ((a + b) * (b + d)))


def CalcTrueSkillStatistic(truthTable) :
    """
    Skill score formula from 
	http://euromet.meteo.fr/resources/ukmeteocal/verification/www/english/msg/ver_categ_forec/uos3/uos3_ko2.htm

    TSS = (ad - bc) / [(a + c)(b + d)]

    Note that a forecast is good when it is closer to 1, and
    is worse if closer to -1.

                Observed
              True    False
Forecasted
    True       a        b
    False      c        d
    """

    a = float(len(truthTable['assocs_Correct']['xLocs']))
    b = float(len(truthTable['assocs_Wrong']['xLocs']))
    c = float(len(truthTable['falarms_Wrong']['xLocs']))
    d = float(len(truthTable['falarms_Correct']['xLocs']))
    if ((a + c) * (b + d)) < 0.1 :
        return 1.0
    else :
        return ((a * d) - (b * c)) / ((a + c) * (b + d))

def FilterMHTTracks(raw_tracks, raw_falarms) :
    """
    This function will 'clean up' the track output from ReadTracks()
    such that the tracks contain only the actual detected points.
    Also, it will re-arrange the tracks in case there are any 1 or 0 length tracks
    over to falarms.
    """
    tracks = copy.deepcopy(raw_tracks['tracks'])
    falarms = copy.deepcopy(raw_falarms)
    
    for aTrack in tracks :
        for index in range(len(aTrack['types'])) :
            if aTrack['types'][index] != 'M' :
		# Flag this element of the track as one to get rid of.
                for aKey in aTrack : 
		    if aKey != 'trackID' : aTrack[aKey][index] = None
		
    (tracks, falarms) = CleanupTracks(tracks, falarms)
    return(tracks, falarms)


def DomainFromTracks(tracks, falarms) :

    minTrackX = []
    maxTrackX = []
    minTrackY = []
    maxTrackY = []
    minTrackT = []
    maxTrackT = []

    for track in tracks :
        minTrackX.append(min(track['xLocs']))
        maxTrackX.append(max(track['xLocs']))
        minTrackY.append(min(track['yLocs']))
        maxTrackY.append(max(track['yLocs']))
        minTrackT.append(min(track['frameNums']))
        maxTrackT.append(max(track['frameNums']))


    for falarm in falarms :
        minTrackX.append(min(falarm['xLocs']))
        maxTrackX.append(max(falarm['xLocs']))
        minTrackY.append(min(falarm['yLocs']))
        maxTrackY.append(max(falarm['yLocs']))
        minTrackT.append(min(falarm['frameNums']))
        maxTrackT.append(max(falarm['frameNums']))

	

    return( [min(minTrackX), max(maxTrackX)],
            [min(minTrackY), max(maxTrackY)],
            [min(minTrackT), max(maxTrackT)] )


def is_eq(val1, val2) :
    """
    Yeah, I know this isn't the smartest thing I have done, but
    most of my code only needs float type math, and it would be
    far to difficult to convert all of the models and such over
    to the "new" decimal type.
    Instead, I just worry about equality with respect to about
    3 decimal places, which is how I am dealing with it for now.

    TODO: Come up with a better way!
    """
#    return int(round(val1 * 1000., 1)) == int(round(val2 * 1000., 1))
    return math.fabs(val1 - val2) < 0.00000001

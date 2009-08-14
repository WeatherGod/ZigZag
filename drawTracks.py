#!/usr/bin/env python


#import sys			# for sys.argv


#fileName = sys.argv[1]




def read_tracks(fileName) :
    contourCnt = None
    falseAlarmCnt = None

    trackCounter = 0
    
    tracks = {'ids': [], 'lens': [], 'tracks': []}
    falseAlarms = []

    for line in open(fileName) :
        line = line.strip()

        if (line.startswith('#')) : continue

        if (contourCnt is None) :
            contourCnt = int(line)
            continue

        if (falseAlarmCnt is None) :
            falseAlarmCnt = int(line)
            continue

        tempList = line.split()
    
        if (len(tracks['tracks']) == trackCounter and trackCounter < contourCnt) :
	    tracks['ids'].append(int(tempList[0]))
	    tracks['lens'].append(int(tempList[1]))
	    tracks['tracks'].append({'types': [],
				     'xLocs': [],
				     'yLocs': [],
				     'frameNums': []})
	    continue

        if (len(tracks['tracks'][-1]['types']) < tracks['lens'][-1]) :
            tracks['tracks'][-1]['types'].append(tempList[0])
	    tracks['tracks'][-1]['xLocs'].append(float(tempList[1]))
	    tracks['tracks'][-1]['yLocs'].append(float(tempList[2]))
	    tracks['tracks'][-1]['frameNums'].append(int(tempList[7]))
            if (len(tracks['tracks'][-1]['types']) == tracks['lens'][-1]) :
		trackCounter += 1
	    continue

        if (len(falseAlarms) < falseAlarmCnt) :
	    falseAlarms.append({'xLoc': float(tempList[0]),
			        'yLoc': float(tempList[1]),
			        'frameNum': int(tempList[2])})

    return(tracks, falseAlarms)


def FilterMHTTracks(raw_tracks) :
    tracks = []

    for aTrack in raw_tracks['tracks'] :
        tracks.append({'xLocs': [xLoc for (xLoc, type) in zip(aTrack['xLocs'], aTrack['types']) if type == 'M'],
		       'yLocs': [yLoc for (yLoc, type) in zip(aTrack['yLocs'], aTrack['types']) if type == 'M'],
		       'frameNums': [frameNum for (frameNum, type) in zip(aTrack['frameNums'], aTrack['types']) if type == 'M']})

    return(tracks)








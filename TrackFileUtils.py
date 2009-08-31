#!/usr/bin/env python

def SaveTracks(simTrackFile, tracks, falarms = None) :
    dataFile = open(simTrackFile, 'r')
    
    dataFile.write("%d" % (len(tracks)))

    if falarms is None :
        dataFile.write("0")
    else :
        dataFile.write("%d" % (len(falarms)))

    for (index, track) in enumerate(tracks) :
        dataFile.write("%d %d" % (index, len(track)))
        


    dataFile.close()



def SaveCorners(inputDataFile, corner_filestem, frameCnt, volume_data) :
    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d\n" % (corner_filestem, frameCnt, 1))

    for (frameNo, aVol) in enumerate(volume_data) :
        outFile = open("%s.%d" % (corner_filestem, frameNo + 1), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write("%d %d " % (strmCell['xLoc'], strmCell['yLoc']) + ' '.join(['0'] * 25) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()

def ReadTracks(fileName) :
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


def SaveCorners(inputDataFile, corner_filestem, frameCnt, volume_data) :
    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d\n" % (corner_filestem, frameCnt, 1))

    for (frameNo, aVol) in enumerate(volume_data) :
        outFile = open("%s.%d" % (corner_filestem, frameNo + 1), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write("%d %d " % (strmCell['xLoc'], strmCell['yLoc']) + ' '.join(['0'] * 25) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()








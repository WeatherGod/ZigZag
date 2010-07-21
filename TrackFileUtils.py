import numpy
import TrackUtils

def SaveTracks(simTrackFile, tracks, falarms = []) :
    dataFile = open(simTrackFile, 'w')
    
    dataFile.write("%d\n" % (len(tracks)))
    dataFile.write("%d\n" % (len(falarms)))

    for (index, track) in enumerate(tracks) :
        dataFile.write("%d %d\n" % (index, len(track)))
        for centroid in track :
	    dataFile.write("%(types)s %(xLocs).10f %(yLocs).10f 0.0 0.0 0.0 0 %(frameNums)d CONSTANT VELOCITY %(cornerIDs)d\n" % 
                            centroid)

    for false_alarm in falarms :
        dataFile.write("%(xLocs).10f %(yLocs).10f %(frameNums)d %(cornerIDs)d\n" % false_alarm[0])
        
    dataFile.close()


def ReadTracks(fileName) :
    contourCnt = None
    falseAlarmCnt = None

    trackCounter = 0
    centroidCnt = 0
    trackLen = 0
    trackID = None
    
    tracks = []
    falseAlarms = []

    for line in open(fileName) :
        line = line.strip()

        if (line.startswith('#')) : continue

        if contourCnt is None :
            contourCnt = int(line)
            continue

        if falseAlarmCnt is None :
            falseAlarmCnt = int(line)
            continue

        tempList = line.split()
    
        if len(tracks) == trackCounter and trackCounter < contourCnt :
            #print "Reading Begining of track   curTrackCnt: %d   trackCounter: %d    contourCnt: %d" % (len(tracks['tracks']), trackCounter, contourCnt)
            centroidCnt = 0
            trackID = int(tempList[0])
            trackLen = int(tempList[1])

	    tracks.append(numpy.empty(trackLen, dtype=TrackUtils.track_dtype))
	    continue

        if contourCnt > 0 and centroidCnt < trackLen :
            #print "Reading Track Element   contourCnt: %d   curTrackLen: %d    trackLen: %d" % (contourCnt, len(tracks['tracks'][-1]['types']), tracks['lens'][-1])
            tracks[-1]['types'][centroidCnt] = tempList[0]
	    tracks[-1]['xLocs'][centroidCnt] = float(tempList[1])
	    tracks[-1]['yLocs'][centroidCnt] = float(tempList[2])
	    tracks[-1]['frameNums'][centroidCnt] = int(tempList[7])
            tracks[-1]['cornerIDs'][centroidCnt] = int(tempList[10])
            centroidCnt += 1
            if centroidCnt == trackLen :
		trackCounter += 1
	    continue

        if len(falseAlarms) < falseAlarmCnt :
            #print "Reading FAlarm"
	    falseAlarms.append(numpy.array([(float(tempList[0]), float(tempList[1]), int(tempList[3]), int(tempList[2]), 'F')],
					   dtype=TrackUtils.track_dtype))

    #print "\n\n\n"

    return tracks, falseAlarms


def SaveCorners(inputDataFile, corner_filestem, frameCnt, volume_data) :
    """
    Save to corner files.
    Corner files comprise of a set of data files, and one control file.
    The control file contains the filestem of the data files, the number of
    data files, and the number of storm cells in each data file.
    """
    startFrame = volume_data[0]['volTime']
    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d\n" % (corner_filestem, frameCnt, startFrame))

    for (frameNo, aVol) in enumerate(volume_data) :
        outFile = open("%s.%d" % (corner_filestem, frameNo + startFrame), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write(("%(xLocs).10f %(yLocs).10f " % (strmCell)) 
                          + ' '.join(['0'] * 25) + ' '
                          + str(strmCell['cornerIDs']) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()

def ReadCorners(inputDataFile) :
    """
    Read corner files.

    inputDataFile is the filename of the 'control file' that contains
    all the info needed to load the corner data files.
    """
    dataFile = open(inputDataFile, 'r')
    headerList = dataFile.readline().split()
    corner_filestem = headerList[0]
    frameCnt = int(headerList[1])
    startFrame = int(headerList[2])

    volume_data = []
    dataFile.close()

    volume_data = [{'volTime': frameNum,
                    # NOTE: .atleast_1d() is used to deal with the edge-case of a single-line file.
                    #       Using loadtxt() on a single-line file will return a file with fewer dimensions
                    #       than expected.
                    # HOWEVER!  This still does not address the issue with empty files!
                    # That situation will cause loadtxt() (and just about all other readers)
                    # to raise an exception.
                    'stormCells': numpy.atleast_1d(numpy.loadtxt("%s.%d" % (corner_filestem, frameNum),
					           dtype=TrackUtils.corner_dtype,
                                                   usecols=(0, 1, 27)))}
                    for frameNum in xrange(startFrame, frameCnt + startFrame)]

    return {'corner_filestem': corner_filestem, 'frameCnt': frameCnt, 'volume_data': volume_data}


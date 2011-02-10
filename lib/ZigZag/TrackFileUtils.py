import numpy
import TrackUtils
import os           # for os.sep

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


def SaveCorners(inputDataFile, corner_filestem, volume_data, path='.') :
    """
    Save to corner files.
    Corner files comprise of a set of data files, and one control file.
    The control file contains the filestem of the data files, the number of
    data files, and the number of storm cells in each data file.
    """
    startFrame = volume_data[0]['volTime']
    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d\n" % (corner_filestem, len(volume_data), startFrame))

    for (frameNo, aVol) in enumerate(volume_data) :
        outFile = open("%s.%d" % (path+os.sep+corner_filestem, frameNo + startFrame), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write(("%(xLocs).10f %(yLocs).10f " % (strmCell)) 
                          + ' '.join(['0'] * 25) + ' '
                          + str(strmCell['cornerIDs']) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()


def SaveTruthTable(trackrun, filestem, truthTable) :
    SaveTracks(filestem + "_" + trackrun + "_Correct.segs", truthTable['assocs_Correct'], truthTable['falarms_Correct'])
    SaveTracks(filestem + "_" + trackrun + "_Wrong.segs", truthTable['assocs_Wrong'], truthTable['falarms_Wrong'])

def ReadTruthTable(trackrun, simParams, true_AssocSegs, true_FAlarmSegs, path='.') :
    """
    NOTE: This is not suitable yet for getting truth tables for Track Plotting!
    """
    correctFilename = path + os.sep + simParams['analysis_stem'] + "_" + trackrun + "_Correct.segs"
    wrongFilename = path + os.sep + simParams['analysis_stem'] + "_" + trackrun + "_Wrong.segs"

    resultFilename = path + os.sep + simParams['result_file'] + "_" + trackrun
    (finalTracks, finalFAlarms) = TrackUtils.FilterMHTTracks(*ReadTracks(resultFilename))

    if (not (os.path.exists(correctFilename) and os.path.exists(wrongFilename))
       or (os.path.getmtime(correctFilename) < os.path.getmtime(resultFilename))
       or (os.path.getmtime(wrongFilename) < os.path.getmtime(resultFilename))) :
        # rebuild the correct and wrong segments files because they either
        # don't exist or the result file is newer than one of the segments files.
        trackerAssocSegs = TrackUtils.CreateSegments(finalTracks)
        trackerFAlarmSegs = TrackUtils.CreateSegments(finalFAlarms)


        #truthTable = TrackUtils.CompareSegments(true_AssocSegs, true_FAlarmSegs,
        #                                        trackerAssocSegs, trackerFAlarmSegs)
        truthTable = TrackUtils.MakeTruthTable(true_AssocSegs, true_FAlarmSegs,
                                                trackerAssocSegs, trackerFAlarmSegs)

        SaveTruthTable(trackrun, path + os.sep + simParams['analysis_stem'], truthTable)

    else :
        # Ok, the results are not newer than the cached truth table segments file, so the
        # cached truth table segments files are valid. So load the cache.
        assocs_Correct, falarms_Correct = TrackUtils.FilterMHTTracks(*ReadTracks(correctFilename))
        assocs_Wrong, falarms_Wrong = TrackUtils.FilterMHTTracks(*ReadTracks(wrongFilename))

        truthTable = {'assocs_Correct': assocs_Correct, 'falarms_Correct': falarms_Correct,
                      'assocs_Wrong': assocs_Wrong, 'falarms_Wrong': falarms_Wrong}

    return truthTable, finalTracks, finalFAlarms


def ReadCorners(inputDataFile, path='.') :
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

    def LoadCorner(filename) :
        try :
            # NOTE: .atleast_1d() is used to deal with the edge-case of a single-line file.
            #       Using loadtxt() on a single-line file will return a file with fewer dimensions
            #       than expected.
            cornerData = numpy.atleast_1d(numpy.loadtxt(filename,
                                                        dtype=TrackUtils.corner_dtype,
                                                        usecols=(0, 1, 27)))
        except IOError as anError :
            if anError.args == ('End-of-file reached before encountering data.',) :
                # This is a corner case of dealing with an empty (but existant!) file.
                # I want these to be treated as empty arrays.
                cornerData = numpy.array([[]], dtype=TrackUtils.corner_dtype)
            else :
                # Some other IOError occurred...
                raise

        return cornerData

    volume_data = [{'volTime': frameNum,
                    'stormCells': LoadCorner("%s.%d" % (path+os.sep+corner_filestem, frameNum))}
                   for frameNum in range(startFrame, frameCnt + startFrame)]

    return {'corner_filestem': corner_filestem, 'frameCnt': frameCnt, 'volume_data': volume_data}

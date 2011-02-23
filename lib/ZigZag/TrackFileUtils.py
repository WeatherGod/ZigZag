import numpy as np
import TrackUtils
import os.path

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

            tracks.append(np.empty(trackLen, dtype=TrackUtils.track_dtype))
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
            falseAlarms.append(np.array([(float(tempList[0]), float(tempList[1]), int(tempList[3]), int(tempList[2]), 'F')],
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
    startFrame = volume_data[0]['frameNum']

    # NOTE: Forces the times to be uniformly spaced...
    timeDelta = np.mean(np.diff([aVol['volTime'] for aVol in volume_data]))

    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d %f\n" % (corner_filestem, len(volume_data), startFrame, timeDelta))

    for volIndex, aVol in enumerate(volume_data) :
        outFile = open("%s.%d" % (os.path.join(path, corner_filestem), startFrame + volIndex), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write(("%(xLocs).10f %(yLocs).10f " % (strmCell)) 
                          + ' '.join(['0'] * 25) + ' '
                          + str(strmCell['cornerIDs']) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()


def SaveTruthTable(trackrun, filestem, truthTable) :
    SaveTracks(filestem + "_" + trackrun + "_Correct.segs",
               truthTable['assocs_Correct'],
               truthTable['falarms_Correct'])
    SaveTracks(filestem + "_" + trackrun + "_Wrong.segs",
               truthTable['assocs_Wrong'],
               truthTable['falarms_Wrong'])
    np.savetxt(filestem + '_' + trackrun + "_Correct.ind", truthTable['correct_indices'])
    np.savetxt(filestem + '_' + trackrun + "_Wrong.ind", truthTable['wrong_indices'])


def ReadTruthTable(trackrun, simParams, true_AssocSegs, true_FAlarmSegs, path='.') :
    """
    NOTE: This is not suitable yet for getting truth tables for Track Plotting!
    """
    correctFilename = os.path.join(path, simParams['analysis_stem'] + "_" + trackrun + "_Correct.segs")
    wrongFilename = os.path.join(path, simParams['analysis_stem'] + "_" + trackrun + "_Wrong.segs")
    corrIndsFilename = os.path.join(path, simParams['analysis_stem'] + "_" + trackrun + "_Correct.ind")
    wrongIndsFilename = os.path.join(path, simParams['analysis_stem'] + "_" + trackrun + "_Wrong.ind")
    resultFilename = os.path.join(path, simParams['result_file'] + "_" + trackrun)
    (finalTracks, finalFAlarms) = TrackUtils.FilterMHTTracks(*ReadTracks(resultFilename))

    result_mtime = os.path.getmtime(resultFilename)

    if (not (os.path.exists(correctFilename) and os.path.exists(wrongFilename)
             and os.path.exists(corrIndsFilename) and os.path.exists(wrongIndsFilename))
       or (os.path.getmtime(correctFilename) < result_mtime)
       or (os.path.getmtime(wrongFilename) < result_mtime)
       or (os.path.getmtime(corrIndsFilename) < result_mtime)
       or (os.path.getmtime(wrongIndsFilename) < result_mtime)) :
        # rebuild the correct and wrong segments files because they either
        # don't exist or the result file is newer than one of the segments files.
        trackerAssocSegs = TrackUtils.CreateSegments(finalTracks)
        trackerFAlarmSegs = TrackUtils.CreateSegments(finalFAlarms)


        #truthTable = TrackUtils.CompareSegments(true_AssocSegs, true_FAlarmSegs,
        #                                        trackerAssocSegs, trackerFAlarmSegs)
        truthTable = TrackUtils.MakeTruthTable(true_AssocSegs, true_FAlarmSegs,
                                                trackerAssocSegs, trackerFAlarmSegs)

        SaveTruthTable(trackrun, os.path.join(path, simParams['analysis_stem']), truthTable)

    else :
        # Ok, the results are not newer than the cached truth table segments file, so the
        # cached truth table segments files are valid. So load the cache.
        assocs_Correct, falarms_Correct = TrackUtils.FilterMHTTracks(*ReadTracks(correctFilename))
        assocs_Wrong, falarms_Wrong = TrackUtils.FilterMHTTracks(*ReadTracks(wrongFilename))
        correct_indices = np.loadtxt(corrIndsFilename).tolist()
        wrong_indices = np.loadtxt(wrongIndsFilename).tolist()
        

        truthTable = {'assocs_Correct': assocs_Correct, 'falarms_Correct': falarms_Correct,
                      'assocs_Wrong': assocs_Wrong, 'falarms_Wrong': falarms_Wrong,
                      'correct_indices': correct_indices,
                      'wrong_indices': wrong_indices}

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
    
    # This last item may or may not exist in various files.
    # When it didn't exist, the frame numbers were assumed to
    # be the same as the time.
    # NOTE, this does assume that the frames are uniformly spaced...
    timeDelta = float(headerList[3]) if len(headerList) > 3 else 1.

    volume_data = []
    dataFile.close()

    def LoadCorner(filename) :
        try :
            # NOTE: .atleast_1d() is used to deal with the edge-case of a single-line file.
            #       Using loadtxt() on a single-line file will return a file with fewer dimensions
            #       than expected.
            cornerData = np.atleast_1d(np.loadtxt(filename,
                                                  dtype=TrackUtils.corner_dtype,
                                                  usecols=(0, 1, 27)))
        except IOError as anError :
            if anError.args == ('End-of-file reached before encountering data.',) :
                # This is a corner case of dealing with an empty (but existant!) file.
                # I want these to be treated as empty arrays.
                cornerData = np.array([], dtype=TrackUtils.corner_dtype)
            else :
                # Some other IOError occurred...
                raise

        return cornerData

    frames = np.arange(startFrame, startFrame + frameCnt)
    volTimes = np.linspace(0.0, (frameCnt - 1)*timeDelta, num=frameCnt)

    volume_data = [{'volTime': volTime,
                    'frameNum': frameNum,
                    'stormCells': LoadCorner("%s.%d" % (os.path.join(path, corner_filestem), frameNum))}
                   for volTime, frameNum in zip(volTimes, frames)]

    return {'corner_filestem': corner_filestem, 'frameCnt': frameCnt, 'volume_data': volume_data}


from __future__ import print_function
import numpy as np
from ZigZag import TrackUtils
import os.path

# A dictionary mapping a field name to the column in a corner file
corner_cols = {'xLocs': 0, 'yLocs': 1, 'sizes':2, 'cornerIDs':27}

# A dictionary mapping a field name to the column in a track file
track_cols = {'xLocs': 1, 'yLocs': 2, 'st_xLocs': 3, 'st_yLocs': 4, 
              'frameNums': 7, 'cornerIDs': 10, 'types': 0}
falarm_cols = {'xLocs': 0, 'yLocs': 1, 'frameNums': 2, 'cornerIDs': 3,
               # These three are not available through the file and are
               # appended on with default values.
               'st_xLocs': -2, 'st_yLocs': -2, 'types': -1}

def SaveTracks(simTrackFile, tracks, falarms=()) :
    dataFile = open(simTrackFile, 'w')

    non_empty = [(len(trk) > 0) for trk in tracks]
    
    dataFile.write("%d\n" % (sum(non_empty)))
    dataFile.write("%d\n" % (len(falarms)))

    for (index, track) in enumerate(tracks) :
        if len(track) == 0 :
            # The track loader function is incapable of loading
            # empty tracks properly.
            continue

        dataFile.write("%d %d\n" % (index, len(track)))
        for centroid in track :
            dataFile.write("%(types)s %(xLocs).10f %(yLocs).10f %(st_xLocs).10f %(st_yLocs).10f 0.0 0 %(frameNums)d CONSTANT VELOCITY %(cornerIDs)d\n" % 
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

    col_converter = {name : np.dtype(dtype) for name, dtype in
                     TrackUtils.base_track_dtype}

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
            trackID = int(tempList[0])
            trackLen = int(tempList[1])

            # Quick sanity check...
            if trackLen == 0 :
                raise ValueError("Empty track %d in %s" % (trackID, fileName))

            #print "Reading Begining of track   curTrackCnt: %d   trackCounter: %d    contourCnt: %d" % (len(tracks['tracks']), trackCounter, contourCnt)
            centroidCnt = 0

            tracks.append(np.empty(trackLen, dtype=TrackUtils.base_track_dtype))
            continue

        if contourCnt > 0 and centroidCnt < trackLen :
            #print "Reading Track Element   contourCnt: %d   curTrackLen: %d    trackLen: %d" % (contourCnt, len(tracks['tracks'][-1]['types']), tracks['lens'][-1])
            tracks[-1][centroidCnt] = tuple([col_converter[name].type(tempList[track_cols[name]]) for
                                             name, typespec in TrackUtils.base_track_dtype])
            #for name, dtype in col_converter.items() :
            #    tracks[-1][centroidCnt][name] = dtype.type(tempList[track_cols[name])
            #tracks[-1]['types'][centroidCnt] = tempList[0]
            #tracks[-1]['xLocs'][centroidCnt] = float(tempList[1])
            #tracks[-1]['yLocs'][centroidCnt] = float(tempList[2])
            #tracks[-1]['frameNums'][centroidCnt] = int(tempList[7])
            #tracks[-1]['cornerIDs'][centroidCnt] = int(tempList[10])
            centroidCnt += 1
            if centroidCnt == trackLen :
                trackCounter += 1

            continue

        if len(falseAlarms) < falseAlarmCnt :
            #print "Reading FAlarm"
            # Adding on some default values for the last few pieces of data
            tempList.extend(['nan', 'F'])
            newArray = np.array([tuple([col_converter[name].type(tempList[falarm_cols[name]]) for
                                       name, typespec in TrackUtils.base_track_dtype])],
                                dtype=TrackUtils.base_track_dtype)
            
            falseAlarms.append(newArray)

    #print "\n\n\n"

    return tracks, falseAlarms


def SaveCorners(inputDataFile, corner_filestem, volume_data, path='.') :
    """
    Save to corner files.
    Corner files comprise of a set of data files, and one control file.
    The control file contains the filestem of the data files, the number of
    data files, and the number of storm cells in each data file.
    """
    if len(volume_data) > 0:
        startFrame = volume_data[0]['frameNum']

        # NOTE: Forces the times to be uniformly spaced...
        timeDelta = np.mean(np.diff([aVol['volTime'] for aVol in volume_data]))
    else:
        startFrame = 0
        timeDelta = 0

    dataFile = open(inputDataFile, 'w')
    dataFile.write("%s %d %d %f\n" % (corner_filestem, len(volume_data),
                                      startFrame, timeDelta))

    # FIXME: Make this more robust and future-proof with respect
    # to texture data.
    for volIndex, aVol in enumerate(volume_data) :
        outFile = open("%s.%d" % (os.path.join(path, corner_filestem), startFrame + volIndex), 'w')
        for strmCell in aVol['stormCells'] :
            outFile.write(("%(xLocs).10f %(yLocs).10f %(sizes).2f " % (strmCell))
                          + ' '.join(['0'] * 24) + ' '
                          + str(strmCell['cornerIDs']) + '\n')
        outFile.close()
        dataFile.write(str(len(aVol['stormCells'])) + '\n')

    dataFile.close()


def _loadtxtfile(filename, loadkwargs, arraykwargs) :
    """
    Stupid wrapper to deal with stupid numpy loadtxt bug where it
    throws an exception if the file is valid, but empty...

    Also, it makes sure that the data isn't squeezed to oblivion...
    """
    # Merge the two dictionaries for the loadtxt kwargs.
    tempdict = dict()
    tempdict.update(loadkwargs, **arraykwargs)
    try :
        # NOTE: .atleast_1d() is used to deal with the edge-case of a single-line file.
        #       Using loadtxt() on a single-line file will return a file with fewer dimensions
        #       than expected.
        data = np.atleast_1d(np.loadtxt(filename, **tempdict))

    except IOError as anError :
        if anError.args == ('End-of-file reached before encountering data.',) :
            # This is a corner case of dealing with an empty (but existant!) file.
            # I want these to be treated as empty arrays.
            data = np.array([], **arraykwargs)
        else :
            # Some other IOError occurred...
            raise

    return data



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

    frames = np.arange(startFrame, startFrame + frameCnt)
    volTimes = np.linspace(0.0, (frameCnt - 1)*timeDelta, num=frameCnt)

    volume_data = [{'volTime': volTime,
                    'frameNum': frameNum,
                    'stormCells': _loadtxtfile("%s.%d" % (os.path.join(path, corner_filestem), frameNum),
                                               dict(usecols=[corner_cols[colname] for colname, typecode in
                                                    TrackUtils.corner_dtype]),
                                               dict(dtype=TrackUtils.corner_dtype))}
                   for volTime, frameNum in zip(volTimes, frames)]
#    print("volume_data:", len(volume_data), " voltimes:", len(volTimes), " frames:", len(frames))
    return {'corner_filestem': corner_filestem, 'frameCnt': frameCnt, 'volume_data': volume_data}


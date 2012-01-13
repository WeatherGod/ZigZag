import os.path
from ZigZag.TrackUtils import *
from ZigZag.TrackFileUtils import *
import ZigZag.ParamUtils as ParamUtils
import numpy as np


def GenerateNewTimes(startFrame, endFrame, frameCnt, skipCnt,
                     startTime, endTime, times=None) :
    newFrames = np.arange(startFrame, endFrame + 1, skipCnt + 1)

    if times is not None :
        start, end = np.searchsorted(times, [startTime, endTime])
        newTimes = times[start:end+1:skipCnt+1]
    else :
        if frameCnt < 2 :
            timeStep = 0.0
        else :
            timeStep = (endTime - startTime) / float(frameCnt - 1)

        newTimes = startTime + timeStep * (newFrames - startFrame)

    assert len(newFrames) == len(newTimes), "Length of newFrames and newTimes do not match."

    return newFrames, newTimes

def _downsample(volData, tLims, skipCnt, times=None) :
    frames = [aVol['frameNum'] for aVol in volData]
    newFrames, newTimes = GenerateNewTimes(min(frames), max(frames), len(frames), skipCnt,
                                           tLims[0], tLims[1], times=times)

    # Resample the volumes, keeping only the selected frames.
    newVols = [aVol for aVol in volData if aVol['frameNum'] in newFrames]

    # Re-number the frames
    for aFrame, aVol in zip(newFrames, newVols) :
        aVol['frameNum'] = aFrame

    return newVols, newFrames, newTimes

def _save_downsample(simParams, newName, newVols, newFrames, newTimes,
                     path='.') :
    simParams['frameCnt'] = len(newFrames)
    simParams['tLims'] = (min(newTimes), max(newTimes))
    simParams['simName'] = newName
    simParams['trackers'] = []
    if simParams['times'] is not None :
        simParams['times'] = newTimes

    ParamUtils.SaveSimulationParams(os.path.join(path, 'simParams.conf'),
                                    simParams)
    SaveCorners(os.path.join(path, simParams['inputDataFile']),
                simParams['corner_file'], newVols, path=path)


def DownsampleCorners(skipCnt, simName, newName, simParams, volData,
                      path='.') :
    # Create the simulation directory.
    newPath = os.path.join(path, newName, '')
    if not os.path.exists(newPath) :
        os.makedirs(newPath)
    else :
        raise ValueError("%s is an existing simulation!" % newPath)

    newVols, newFrames, newTimes = _downsample(volData, simParams['tLims'],
                                               skipCnt,
                                               times=simParams['times'])

    _save_downsample(simParams, newName, newVols, newFrames, newTimes,
                     path=newPath)

def DownsampleTracks(skipCnt, simName, newName, simParams,
                     origTracks, tracks, volData,
                     path='.', retain_framenums=False) :

    # Create the simulation directory.
    newPath = os.path.join(path, newName, '')
    if not os.path.exists(newPath) :
        os.makedirs(newPath)
    else :
        raise ValueError("%s is an existing simulation!" % newPath)

    newVols, newFrames, newTimes = _downsample(volData, simParams['tLims'],
                                               skipCnt,
                                               times=simParams['times'])
    replaceFrames = {frame:(index + 1) for
                      index, frame in enumerate(newFrames)}

    newTracks = [FilterTrack(aTrack, newFrames) for
                 aTrack in tracks[0]]
    newFAlarms = [FilterTrack(aTrack, newFrames) for
                  aTrack in tracks[1]]
    origTracks_down = [FilterTrack(aTrack, newFrames) for
                       aTrack in origTracks[0]]
    origFAlarms_down = [FilterTrack(aTrack, newFrames) for
                        aTrack in origTracks[1]]

    if not retain_framenums :
        ReplaceFrameInfo(newTracks, replaceFrames)
        ReplaceFrameInfo(newFAlarms, replaceFrames)
        ReplaceFrameInfo(origTracks_down, replaceFrames)
        ReplaceFrameInfo(origFAlarms_down, replaceFrames)

    CleanupTracks(newTracks, newFAlarms)
    # NOTE: I am wary of cleaning up original tracks, but
    #       I don't know how well the file utilities will
    #       handle empty tracks
    CleanupTracks(origTracks_down, origFAlarms_down)

    # Maybe set if a new bbox is requested?
    #xLims, yLims, tLims = DomainFromTracks(newTracks, newFAlarms)
    #simParams['xLims'] = xLims
    #simParams['yLims'] = yLims

    SaveTracks(os.path.join(newPath, simParams['simTrackFile']),
               origTracks_down, origFAlarms_down)
    SaveTracks(os.path.join(newPath, simParams['noisyTrackFile']),
               newTracks, newFAlarms)

    _save_downsample(simParams, newName, newVols, newFrames, newTimes,
                     path=newPath)


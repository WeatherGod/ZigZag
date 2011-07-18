import os.path
from ZigZag.TrackUtils import *
from ZigZag.TrackFileUtils import *
import ZigZag.ParamUtils as ParamUtils
import numpy as np


def GenerateNewTimes(startFrame, endFrame, frameCnt, skipCnt,
                     startTime, endTime) :
    newFrames = np.arange(startFrame, endFrame + 1, skipCnt + 1)

    if frameCnt < 2 :
        timeStep = 0.0
    else :
        timeStep = (endTime - startTime) / float(frameCnt - 1)

    newTimes = startTime + timeStep * (newFrames - startFrame)

    return newFrames, newTimes

def _downsample(volData, tLims, skipCnt) :
    frames = [aVol['frameNum'] for aVol in volData]
    newFrames, newTimes = GenerateNewTimes(min(frames), max(frames), len(frames), skipCnt,
                                           tLims[0], tLims[1])

    # Resample the volumes, keeping only the selected frames.
    newVols = [aVol for aVol in volData if aVol['frameNum'] in newFrames]

    # Re-number the frames
    for aFrame, aVol in zip(newFrames, newVols) :
        aVol['frameNum'] = aFrame

    return newVols, newFrames, newTimes


def DownsampleCorners(skipCnt, simName, newName, simParams, volData, path='.') :
    # Create the simulation directory.
    newPath = os.path.join(path, newName, '')
    if not os.path.exists(newPath) :
        os.makedirs(newPath)
    else :
        raise ValueError("%s is an existing simulation!" % newPath)

    newVols, newFrames, newTimes = _downsample(volData, simParams['tLims'], skipCnt)

    simParams['frameCnt'] = len(newFrames)
    simParams['tLims'] = (min(newTimes), max(newTimes))
    simParams['simName'] = newName
    simParams['trackers'] = []

    dirName = os.path.join(path, simParams['simName'])
    ParamUtils.SaveSimulationParams(os.path.join(dirName, 'simParams.conf'), simParams)
    SaveCorners(os.path.join(dirName, simParams['inputDataFile']),
                simParams['corner_file'], newVols, path=dirName)

def DownsampleTracks(skipCnt, simName, newName, simParams,
                     origTracks, tracks, volData,
                     path='.', retain_framenums=False) :

    # Create the simulation directory.
    newPath = os.path.join(path, newName, '')
    if not os.path.exists(newPath) :
        os.makedirs(newPath)
    else :
        raise ValueError("%s is an existing simulation!" % newPath)

    # FIXME: This isn't quite right, but it might be easily fixed.
    #        Heck, it might actually already be right.
    #        The question is that do we assume that we always know
    #        what the range of frame numbers are from knowing the
    #        frameCnt, or do we always derive it from the tracks?
    #        It might be better to assume it from the frameCnt
    #        and grab it from the frameCnt...
    #xLims, yLims, frameLims = DomainFromTracks(*tracks)
    #newFrames, newTimes = GenerateNewTimes(frameLims[0], frameLims[1], simParams['frameCnt'], skipCnt,
    #                                       simParams['tLims'][0], simParams['tLims'][1])

    # Trying another approach...
    newVols, newFrames, newTimes = _downsample(volData, simParams['tLims'],
                                               skipCnt)
    tLims = (newTimes.min(), newTimes.max())
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

    # Commenting it out for the new approach
    #volData = CreateVolData(newTracks, newFAlarms,
    #                        newFrames, tLims, xLims, yLims)

    simParams['frameCnt'] = len(newFrames)
    # Maybe set if a new bbox is requested?
    #simParams['xLims'] = xLims
    #simParams['yLims'] = yLims
    simParams['tLims'] = tLims
    simParams['simName'] = newName
    simParams['trackers'] = []


    dirName = os.path.join(path, simParams['simName'])
    ParamUtils.SaveSimulationParams(os.path.join(dirName, "simParams.conf"), simParams)
    SaveTracks(os.path.join(dirName, simParams['simTrackFile']), origTracks_down,
                                                                 origFAlarms_down)
    SaveTracks(os.path.join(dirName, simParams['noisyTrackFile']), newTracks,
                                                                   newFAlarms)
    SaveCorners(os.path.join(dirName, simParams['inputDataFile']),
                simParams['corner_file'], newVols, path=dirName)



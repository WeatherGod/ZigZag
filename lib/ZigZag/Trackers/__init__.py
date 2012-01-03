
import ZigZag.TrackFileUtils as TrackFileUtils
import ZigZag.TrackUtils as TrackUtils
import os.path
import tempfile
import os


trackerList = {}
param_confList = {}
def _register_tracker(tracker, name, param_conf) :
    if name in trackerList :
        raise ValueError("%s is already a registered tracker." % name)

    param_conf['algorithm'] = "string()"
    trackerList[name] = tracker
    param_confList[name] = param_conf
    



def SCIT_Track(trackRun, simParams, trackParams, returnResults=True, path='.') :
    import scit
    dirName = path
    cornerInfo = TrackFileUtils.ReadCorners(os.path.join(dirName,
                                                 simParams['inputDataFile']),
                                            path=dirName)
    speedThresh = float(trackParams['speedThresh'])
    framesBack = int(trackParams['framesBack'])

    if simParams['frameCnt'] <= 1 :
        raise Exception("Not enough frames for tracking: %d" %
                         simParams['frameCnt'])

    tDelta = ((simParams['tLims'][1] - simParams['tLims'][0]) /
              float(simParams['frameCnt'] - 1))
    strmAdap = {'distThresh': speedThresh * tDelta,
                'framesBack': framesBack}
    stateHist = []
    strmTracks = []
    infoTracks = []

    for aVol in cornerInfo['volume_data'] :
        scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol)

    scit.EndTracks(stateHist, strmTracks)

    falarms = []
    TrackUtils.CleanupTracks(strmTracks, falarms)
    TrackFileUtils.SaveTracks(os.path.join(dirName,
                                     simParams['result_file'] + "_" + trackRun),
                              strmTracks, falarms)

    if returnResults :
        return strmTracks, falarms

_register_tracker(SCIT_Track, "SCIT",
                  dict(speedThresh="float(min=0.0)",
                       framesBack="integer(min=0, default=10)"))

def MHT_Track(trackRun, simParams, trackParams, returnResults=True, path='.') :
    import mht
    progDir = "~/Programs/mht_tracking/tracking/"
    dirName = path
    # Popping off the ParamFile key so that the rest of the available
    # configs can be used for making the MHT parameter file.
#    paramDir, paramName = os.path.split(trackParams.pop("ParamFile"))
#    file, paramFile = tempfile(prefix=paramName,
#                               dir=os.path.join(dirName, paramDir)
    paramFile, paramName = tempfile.mkstemp(text=True)
    # Don't need it open, just pass the name along.
    os.close(paramFile)

    # Temporary popping...
    trackParams.pop("algorithm")

    mht.SaveMHTParams(paramName, trackParams)
    resultFile = os.path.join(dirName, simParams['result_file'] +
                                       '_' + trackRun)

    retcode = mht.track(resultFile, paramName,
                        os.path.join(dirName, simParams['inputDataFile']),
                        dirName)
    
    if retcode != 0 :
        raise Exception("MHT Tracker failed! ResultFile: %s ParamFile: %s" %
                        (resultFile, paramName))

    os.remove(paramName)

    if returnResults :
        tracks = TrackFileUtils.ReadTracks(resultFile)
        return TrackUtils.FilterMHTTracks(*tracks)

_register_tracker(MHT_Track, "MHT",
                  dict(varx="float(min=0.0, default=1.0)",
                       vary="float(min=0.0, default=1.0)",
                       vargrad="float(min=0.0, default=0.01)",
                       varint="float(min=0.0, default=100.0)",
                       varproc="float(min=0.0, default=0.5)",
                       pod="float(min=0.0, default=0.9999)",
                       lambdax="float(min=0.0, default=20.0)",
                       ntps="float(min=0.0, default=0.004)",
                       mfaps="float(min=0.0, default=0.0002)",
                       mxghpg="integer(min=1, default=300)",
                       mxdpth="integer(min=0, default=3)",
                       mnratio="float(min=0.0, default=0.001)",
                       intthrsh="float(min=0.0, default=0.90)",
                       mxdist="float(min=0.0, default=5.9)",
                       varvel="float(min=0.0, default=200.0)",
                       frames="integer(min=1, default=999999)",
                       ParamFile="string(default='Parameters')"))

def TITAN_Track(trackRun, simParams, trackParams,
                returnResults=True, path='.') :
    import titan
    dirName = path
    cornerInfo = TrackFileUtils.ReadCorners(os.path.join(dirName,
                                                    simParams['inputDataFile']),
                                            path=dirName)
    speedThresh = float(trackParams['speedThresh'])

    if simParams['frameCnt'] <= 1 :
        raise Exception("Not enough frames for tracking: %d" %
                         simParams['frameCnt'])

    tDelta = ((simParams['tLims'][1] - simParams['tLims'][0]) /
              float(simParams['frameCnt'] - 1))

    t = titan.TITAN(distThresh=speedThresh*tDelta)
    for aVol in cornerInfo['volume_data'] :
        t.TrackStep(aVol)

    # Tidy up tracks because there won't be any more data
    t.finalize()

    tracks = t.tracks
    falarms = []
    TrackUtils.CleanupTracks(tracks, falarms)
    TrackFileUtils.SaveTracks(os.path.join(dirName, simParams['result_file'] +
                                                    "_" + trackRun),
                              tracks, falarms)

    if returnResults :
        return tracks, falarms

_register_tracker(TITAN_Track, "TITAN", dict(speedThresh="float(min=0.0)"))

def ASCIT_Track(trackRun, simParams, trackParams,
                returnResults=True, path='.') :
    import ascit
    dirName = path
    cornerInfo = TrackFileUtils.ReadCorners(os.path.join(dirName,
                                                    simParams['inputDataFile']),
                                            path=dirName)
    speedThresh = float(trackParams['speedThresh'])

    if simParams['frameCnt'] <= 1 :
        raise Exception("Not enough frames for tracking: %d" %
                         simParams['frameCnt'])

    tDelta = ((simParams['tLims'][1] - simParams['tLims'][0]) /
              float(simParams['frameCnt'] - 1))

    t = ascit.ASCIT(distThresh=speedThresh*tDelta,
                    framesBack=int(trackParams['framesBack']))
    for aVol in cornerInfo['volume_data'] :
        t.TrackStep(aVol)

    # Tidy up tracks because there won't be any more data
    t.finalize()

    tracks = t.tracks
    falarms = []
    TrackUtils.CleanupTracks(tracks, falarms)
    TrackFileUtils.SaveTracks(os.path.join(dirName, simParams['result_file'] +
                                                    "_" + trackRun),
                              tracks, falarms)

    if returnResults :
        return tracks, falarms

_register_tracker(ASCIT_Track, "ASCIT",
                  dict(speedThresh="float(min=0.0)",
                       framesBack="integer(min=0, default=10)"))


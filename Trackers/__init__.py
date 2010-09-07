import scit
import TrackFileUtils
import TrackUtils
import os


trackerList = {}
def _register_tracker(tracker, name) :
    if name in trackerList :
        raise ValueError("%s is already a registered tracker." % name)

    trackerList[name] = tracker



def SCIT_Track(simParams, trackParams, returnResults=True, path='.') :
    dirName = path + os.sep + simParams['simName']
    cornerInfo = TrackFileUtils.ReadCorners(dirName + os.sep + simParams['inputDataFile'], path=path)
    strmAdap = {'distThresh': float(trackParams['distThresh'])}
    stateHist = []
    strmTracks = []
    infoTracks = []

    for aVol in cornerInfo['volume_data'] :
        scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol)

    scit.EndTracks(stateHist, strmTracks)

    falarms = []
    TrackUtils.CleanupTracks(strmTracks, falarms)
    TrackFileUtils.SaveTracks(simParams['result_file'] + "_SCIT", strmTracks, falarms)

    if returnResults :
        return strmTracks, falarms

_register_tracker(SCIT_Track, "SCIT")

def MHT_Track(simParams, trackParams, returnResults=True, path='.') :
    progDir = "~/Programs/mht_tracking/tracking/"
    paramFile = trackParams.pop("ParamFile")
    dirName = path + os.sep + simParams['simName']

    paramArgs = "python %smakeparams.py %s" % (progDir, path + os.sep + paramFile)
    for key, val in trackParams.items() :
        paramArgs += " --%s %s" % (key, val)

    print paramArgs
    os.system(paramArgs)

    theCommand = "%strackCorners -o %s -p %s -i %s -d %s > /dev/null" % (progDir,
                                            dirName + os.sep + simParams['result_file'] + "_MHT",
                                            path + os.sep + paramFile,
                                            dirName + os.sep + simParams['inputDataFile'],
                                            path)
    
    print theCommand
    os.system(theCommand)

    if returnResults :
        return TrackUtils.FilterMHTTracks(*TrackFileUtils.ReadTracks(dirName + os.sep + trackParams['result_file'] + "_MHT"))

_register_tracker(MHT_Track, "MHT")


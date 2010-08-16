import scit
import TrackFileUtils
import TrackUtils
import os


trackerList = {}
def _register_tracker(tracker, name) :
    if name in trackerList :
        raise ValueError("%s is already a registered tracker." % name)

    trackerList[name] = tracker



def SCIT_Track(simParams, trackParams, returnResults=True) :
    cornerInfo = TrackFileUtils.ReadCorners(simParams['inputDataFile'])
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

def MHT_Track(simParams, trackParams, returnResults=True) :
    progDir = "~/Programs/mht_tracking/tracking/"
    paramFile = trackParams.pop("ParamFile")

    paramArgs = "python %smakeparams.py %s" % (progDir, paramFile)
    for key, val in trackParams.items() :
        paramArgs += " --%s %s" % (key, val)

    os.system(paramArgs)

    theCommand = "%strackCorners -o %s -p %s -i %s > /dev/null" % (progDir,
                                            simParams['result_file'] + "_MHT",
                                            paramFile,
                                            simParams['inputDataFile'])
    
    print theCommand
    os.system(theCommand)

    if returnResults :
        return TrackUtils.FilterMHTTracks(*TrackFileUtils.ReadTracks(trackParams['result_file'] + "_MHT"))

_register_tracker(MHT_Track, "MHT")


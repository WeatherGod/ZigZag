import scit
import TrackFileUtils
import TrackUtils
import os


trackerList = {}
def _register_tracker(tracker, name) :
    if name in trackerList :
        raise ValueError("%s is already a registered tracker." % name)

    trackerList[name] = tracker



def SCIT_Track(trackParams, returnResults=True) :
    cornerInfo = TrackFileUtils.ReadCorners(trackParams['inputDataFile'])
    strmAdap = {'distThresh':5.0}
    stateHist = []
    strmTracks = []
    infoTracks = []

    for aVol in cornerInfo['volume_data'] :
        scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol)

    scit.EndTracks(stateHist, strmTracks)

    falarms = []
    TrackUtils.CleanupTracks(strmTracks, falarms)
    TrackFileUtils.SaveTracks(trackParams['result_file'] + "_SCIT", strmTracks, falarms)

    if returnResults :
        return strmTracks, falarms

_register_tracker(SCIT_Track, "SCIT")

def MHT_Track(trackParams, returnResults=True) :
    progDir = "~/Programs/mht_tracking/tracking/"
    theCommand = "%strackCorners -o %s -p %s -i %s > /dev/null" % (progDir,
                                            trackParams['result_file'] + "_MHT",
                                            trackParams['ParamFile'],
                                            trackParams['inputDataFile'])
    
    print theCommand
    os.system(theCommand)

    if returnResults :
        return TrackUtils.FilterMHTTracks(*TrackFileUtils.ReadTracks(trackParams['result_file'] + "_MHT"))

_register_tracker(MHT_Track, "MHT")


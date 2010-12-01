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
    cornerInfo = TrackFileUtils.ReadCorners(dirName + os.sep + simParams['inputDataFile'], path=dirName)
    strmAdap = {'distThresh': float(trackParams['distThresh'])}
    stateHist = []
    strmTracks = []
    infoTracks = []

    for aVol in cornerInfo['volume_data'] :
        scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol)

    scit.EndTracks(stateHist, strmTracks)

    falarms = []
    TrackUtils.CleanupTracks(strmTracks, falarms)
    TrackFileUtils.SaveTracks(dirName + os.sep + simParams['result_file'] + "_SCIT",
                              strmTracks, falarms)

    if returnResults :
        return strmTracks, falarms

_register_tracker(SCIT_Track, "SCIT")

def MHT_Track(simParams, trackParams, returnResults=True, path='.') :
    progDir = "~/Programs/mht_tracking/tracking/"
    # Popping off the ParamFile key so that the rest of the available
    # configs can be used for making the MHT parameter file.
    paramFile = trackParams.pop("ParamFile")
    dirName = path + os.sep + simParams['simName']

    paramArgs = "python %smakeparams.py %s" % (progDir, dirName + os.sep + paramFile)
    for key, val in trackParams.items() :
        paramArgs += " --%s %s" % (key, val)

    print paramArgs
    # TODO: Temporary until I fix this to use Popen()
    if os.system(paramArgs) != 0 :
        raise Exception("MHT Param-maker failed!")
        

    theCommand = "%strackCorners -o %s -p %s -i %s -d %s > /dev/null" % (progDir,
                                            dirName + os.sep + simParams['result_file'] + "_MHT",
                                            dirName + os.sep + paramFile,
                                            dirName + os.sep + simParams['inputDataFile'],
                                            dirName)
    
    print theCommand
    # TODO: Temporary until I fix this to use Popen()
    if os.system(theCommand) != 0 :
        raise Exception("MHT tracker failed!")

    if returnResults :
        return TrackUtils.FilterMHTTracks(*TrackFileUtils.ReadTracks(dirName + os.sep + trackParams['result_file'] + "_MHT"))

_register_tracker(MHT_Track, "MHT")



import ZigZag.TrackFileUtils as TrackFileUtils
import ZigZag.TrackUtils as TrackUtils
import os.path


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
    cornerInfo = TrackFileUtils.ReadCorners(os.path.join(dirName, simParams['inputDataFile']), path=dirName)
    speedThresh = float(trackParams['speedThresh'])

    if simParams['frameCnt'] <= 1 :
        raise Exception("Not enough frames for tracking: %d" % simParams['frameCnt'])

    tDelta = (simParams['tLims'][1] - simParams['tLims'][0]) / float(simParams['frameCnt'] - 1)
    strmAdap = {'distThresh': speedThresh * tDelta}
    stateHist = []
    strmTracks = []
    infoTracks = []

    for aVol in cornerInfo['volume_data'] :
        scit.TrackStep_SCIT(strmAdap, stateHist, strmTracks, infoTracks, aVol)

    scit.EndTracks(stateHist, strmTracks)

    falarms = []
    TrackUtils.CleanupTracks(strmTracks, falarms)
    TrackFileUtils.SaveTracks(os.path.join(dirName, simParams['result_file'] + "_" + trackRun),
                              strmTracks, falarms)

    if returnResults :
        return strmTracks, falarms

_register_tracker(SCIT_Track, "SCIT", dict(speedThresh="float(min=0.0)"))

def MHT_Track(trackRun, simParams, trackParams, returnResults=True, path='.') :
    progDir = "~/Programs/mht_tracking/tracking/"
    # Popping off the ParamFile key so that the rest of the available
    # configs can be used for making the MHT parameter file.
    paramFile = trackParams.pop("ParamFile")
    # Temporary popping...
    trackParams.pop("algorithm")
    dirName = path

    paramArgs = "python %smakeparams.py %s" % (progDir, os.path.join(dirName, paramFile))
    for key, val in trackParams.items() :
        paramArgs += " --%s %s" % (key, val)

    print paramArgs
    # TODO: Temporary until I fix this to use Popen()
    if os.system(paramArgs) != 0 :
        raise Exception("MHT Param-maker failed!")
        

    theCommand = "%strackCorners -o %s -p %s -i %s -d %s > /dev/null" % (progDir,
                                os.path.join(dirName, simParams['result_file'] + "_" + trackRun),
                                os.path.join(dirName, paramFile),
                                os.path.join(dirName, simParams['inputDataFile']),
                                dirName)
    
    print theCommand
    # TODO: Temporary until I fix this to use Popen()
    if os.system(theCommand) != 0 :
        raise Exception("MHT tracker failed!")

    if returnResults :
        return TrackUtils.FilterMHTTracks(*TrackFileUtils.ReadTracks(os.path.join(dirName, trackParams['result_file'] + "_" + trackRun)))

_register_tracker(MHT_Track, "MHT", dict(varx="float(min=0.0, default=1.0)",
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


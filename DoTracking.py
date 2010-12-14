#!/usr/bin/env python

import Trackers
import ParamUtils	  # for reading simParams files
import os                               # for os.sep


def SingleTracking(simFile, simParams, trackConfs, path='.') :
    #simParams['trackers'] = trackConfs.keys()

    storedConfFile = path + os.sep + simParams['simName'] + os.sep + simParams['trackerparams']
    if not os.path.exists(storedConfFile) :
        ParamUtils.SaveConfigFile(storedConfFile, {})
    storedTrackConfs = ParamUtils.LoadTrackerParams([storedConfFile], None)

    for trackRun in trackConfs :
        tracker = trackConfs[trackRun]['algorithm']
        Trackers.trackerList[tracker](trackRun, simParams.copy(), trackConfs[trackRun].copy(),
                                      returnResults=False, path=path)

        # We want this simulation to know which trackers they used,
        # so we will update the file after each successful tracking operation.
        # Note that we still want an ordered, unique list, henced the use of
        # set() and .sort()
        simParams['trackers'].append(trackRun)
        tempHold = list(set(simParams['trackers']))
        tempHold.sort()
        simParams['trackers'] = tempHold
        ParamUtils.SaveSimulationParams(simFile, simParams)

        storedTrackConfs[trackRun] = trackConfs[trackRun].copy()
        ParamUtils.SaveConfigFile(storedConfFile, storedTrackConfs)


if __name__ == "__main__" :
    import argparse       # Command-line parsing

    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')

    args = parser.parse_args()

    dirName = args.directory + os.sep + args.simName
    simFile = dirName + os.sep + "simParams.conf"
    simParams = ParamUtils.ReadSimulationParams(simFile)
    
    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs, simParams)

    SingleTracking(simFile, simParams, trackConfs.dict(), path=args.directory)



#!/usr/bin/env python

import Trackers
import ParamUtils	  # for reading simParams files


def SingleTracking(simFile, simParams, trackConfs, path='.') :
    simParams['trackers'] = trackConfs.keys()
    # We want this simulation to know which trackers they used.
    ParamUtils.SaveSimulationParams(simFile, simParams.copy())

    for trackRun in trackConfs :
        tracker = trackConfs[trackRun]['algorithm']
        Trackers.trackerList[tracker](trackRun, simParams.copy(), trackConfs[trackRun].copy(),
                                      returnResults=False, path=path)


if __name__ == "__main__" :
    import argparse       # Command-line parsing
    import os                               # for os.sep.join()

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



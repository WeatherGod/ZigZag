#!/usr/bin/env python

import Trackers
import ParamUtils	  # for reading simParams files


def SingleTracking(simFile, trackConfs) :
    simParams = ParamUtils.ReadSimulationParams(simFile)
    simParams['trackers'] = list(trackConfs)
    # We want this simulation to know which trackers they used.
    ParamUtils.SaveSimulationParams(simFile, simParams.copy())

    for tracker in trackConfs :
        Trackers.trackerList[tracker](simParams.copy(), trackConfs[tracker].copy(),
                                      returnResults=False)


if __name__ == "__main__" :
    import argparse       # Command-line parsing
    from configobj import ConfigObj
    import os                               # for os.sep.join()

    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")

    args = parser.parse_args()

    trackConfs = ConfigObj()
    for file in args.trackconfs :
        partConf = ConfigObj(file)
        trackConfs.merge(partConf)

    simFile = args.simName + os.sep + "simParams.conf"
    SingleTracking(simFile, trackConfs.dict())


#!/usr/bin/env python

import ParamUtils
import Trackers
from configobj import ConfigObj

import os                               # for os.sep.join(), os.system()

if __name__ == "__main__" :
    import ParamUtils	  # for reading simParams files
    import argparse       # Command-line parsing
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

    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.simName, "simParams.conf"]))

    #simParams['ParamFile'] = os.sep.join([args.simName, "Parameters"])
    
    for tracker in trackConfs :
        Trackers.trackerList[tracker](simParams, trackConfs[tracker], returnResults=False)



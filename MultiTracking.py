#!/usr/bin/env python

import os
import Trackers
from DoTracking import SingleTracking
import ParamUtils     # for reading simParams files

def MultiTrack(multiSimParams, trackConfs) :


    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%s%s%.3d" % (multiSimParams['simName'],
                                os.sep, index)
        print "Sim:", simName
        paramFile = simName + os.sep + "simParams.conf"
        simParams = ParamUtils.ReadSimulationParams(paramFile)
        SingleTracking(paramFile, simParams, trackConfs.copy())


if __name__ == '__main__' :
    import argparse       # Command-line parsing


    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")

    args = parser.parse_args()

    paramFile = args.simName + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    trackConfs = ParamUtils._loadTrackerParams(args.trackconfs, multiSimParams)

    MultiTrack(multiSimParams, trackConfs.dict())



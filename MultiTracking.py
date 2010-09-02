#!/usr/bin/env python

import os
import Trackers
from DoTracking import SingleTracking
import ParamUtils     # for reading simParams files

def MultiTrack(multiSimParams, trackConfs, path='.') :
    dirName = path + os.sep + multiSimParams['simName']

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%.3d" % index
        print "Sim:", simName
        paramFile = dirName + os.sep + simName + os.sep + "simParams.conf"
        simParams = ParamUtils.ReadSimulationParams(paramFile)
        SingleTracking(paramFile, simParams, trackConfs.copy(), path=dirName)


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
    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs, multiSimParams)

    MultiTrack(multiSimParams, trackConfs.dict())



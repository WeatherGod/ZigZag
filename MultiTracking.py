#!/usr/bin/env python

import os
import Trackers
from DoTracking import SingleTracking
import ParamUtils     # for reading simParams files

def MultiTrack(multiSimParams, trackConfs, path='.') :
    dirName = path + os.sep + multiSimParams['simName']

    simCnt = int(multiSimParams['simCnt'])

    for index in range(simCnt) :
        simName = "%.3d" % index
        print "Sim:", simName
        paramFile = dirName + os.sep + simName + os.sep + "simParams.conf"
        simParams = ParamUtils.ReadSimulationParams(paramFile)

        # A copy of trackConfs is used here because the tracker calls could
        # modify the contents of trackConfs, and we don't want those changes
        # to propagate to subsequent calls to SingleTracking()
        SingleTracking(paramFile, simParams, trackConfs.copy(), path=dirName)


if __name__ == '__main__' :
    import argparse       # Command-line parsing


    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("multiSim",
                      help="Generate Tracks for MULTISIM",
                      metavar="MULTISIM")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM",
                        metavar="DIRNAME", default='.')

    args = parser.parse_args()

    paramFile = args.directory + os.sep + args.multiSim + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)

    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs, multiSimParams)

    MultiTrack(multiSimParams, trackConfs.dict(), path=args.directory)



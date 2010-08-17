#!/usr/bin/env python

import os
import Trackers
from DoTracking import SingleTracking
import ParamUtils     # for reading simParams files

def MultiTrack(paramFile, trackConfs) :
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%s%s%.3d" % (multiSimParams['simName'],
                                os.sep, index)
        print "Sim:", simName
        simFile = simName + os.sep + "simParams.conf"
        SingleTracking(simFile, trackConfs.copy())


if __name__ == '__main__' :
    import argparse       # Command-line parsing
    from configobj import ConfigObj


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

    MultiTrack("%s%sMultiSim.ini" % (args.simName, os.sep), trackConfs.dict())



#!/usr/bin/env python


if __name__ == '__main__' :
    import ParamUtils     # for reading simParams files
    import argparse       # Command-line parsing
    from configobj import ConfigObj
    import os
    import Trackers

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

    multiSimParams = ParamUtils.Read_MultiSim_Params("%s%sMultiSim.ini" % (args.simName, os.sep))

    for index in range(int(multiSimParams['simCnt'])) :
        simName = "%s%s%.3d" % (multiSimParams['simName'],
                                os.sep, index)
        print "Sim:", simName
        simFile = simName + os.sep + "simParams.conf"
        simParams = ParamUtils.ReadSimulationParams(simFile)
        simParams['trackers'] = list(trackConfs)
        # We want these sub-simulations to know which trackers they used.
        ParamUtils.SaveSimulationParams(simFile, simParams.copy())
        
        for tracker in trackConfs :
            print "   Tracker:", tracker
            Trackers.trackerList[tracker](simParams.copy(), trackConfs[tracker].dict(),
                                          returnResults=False)


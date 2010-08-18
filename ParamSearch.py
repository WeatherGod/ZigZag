#!/usr/bin/env python

from MultiAnalysis import MultiAnalyze
from MultiTracking import MultiTrack

if __name__ == '__main__' :
    import argparse
    import os           # for os.sep

    parser = argparse.ArgumentParser(description='Search for optimal parameters for a tracker for a given multi-sim')
    parser.add_argument("simName",
                      help="Analyze tracks for SIMNAME",
                      metavar="SIMNAME")
    parser.add_argument("tracker", help="The tracker to use", metavar="TRACKER")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")

    args = parser.parse_args()
    paramFile = args.simName + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    trackConfs = ParamUtils._loadTrackerParams(args.trackConfs.keys(), multiSimParams)

    # Get only the one tracker I want
    trackConfs = {args.tracker: trackConfs.pop(args.tracker)}

    paramVals = [0.9999, 0.999, 0.99, 0.9]
    for val in paramVals :
        trackConfs[args.tracker]['pod'] = val
        # TODO: still need to modify the destination of the result files
        MultiTrack(multiSimParams, trackConfs.dict())


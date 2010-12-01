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
    parser.add_argument("confFiles", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')


    # Food for thought... two approaches
    # 1.
    # Take a single simulation, and makes it into a 'multi-sim' of sorts
    # Each sub simulation of the multi-sim has the same simulation, but has a
    # different tracking done to it.
    # This makes it very easy for MultiAnalysis and other programs to pick up and use,
    # but it makes a *huge* bloat in files.

    # 2.
    # Take a single simulation, but produce a different track result file for
    # each tracker.  Less redundancy in files, but makes it hard to analyze results.


    args = parser.parse_args()
    paramFile = args.directory + os.sep + args.simName + os.sep + "MultiSim.ini"
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    trackConfs = ParamUtils.LoadTrackerParams(args.confFiles, multiSimParams)

    # Get only the one tracker I want
    trackConfs = {args.tracker: trackConfs.pop(args.tracker)}

    paramVals = [0.9999, 0.999, 0.99, 0.9]
    for val in paramVals :
        trackConfs[args.tracker]['pod'] = val

        # TODO: still need to modify the destination of the result files
        MultiTrack(multiSimParams, trackConfs.dict(), path=args.directory)


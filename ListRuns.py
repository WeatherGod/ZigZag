#!/usr/bin/env python

import fnmatch

def ExpandTrackRuns(allTrackRuns, requestedRuns=None) :
    """
    Some requested runs may have glob-like search expressions.
    This resolves those expressions and returns a list of requested
    runs fully qualified.
    """
    if requestedRuns is None :
        return allTrackRuns

    expandedAll = []
    for aRun in requestedRuns :
        matches = fnmatch.filter(allTrackRuns, aRun)
        if len(matches) == 0 :
            raise ValueError("Could not find a track to match: " + aRun)
        expandedAll.extend(matches)

    return expandedAll


if __name__ == '__main__' :
    import os
    import argparse
    import ParamUtils

    parser = argparse.ArgumentParser(description="List the trackruns for a simulation.")
    parser.add_argument("simName",
                        help="List track runs done for SIMNAME", metavar="SIMNAME")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')
    parser.add_argument("-t", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to list.  List all runs if none are given.",
                        metavar="RUN", default=None)

    args = parser.parse_args()

    dirName = args.directory + os.sep + args.simName
    paramFile = dirName + os.sep + "simParams.conf"
    simParams = ParamUtils.ReadSimulationParams(paramFile)

    trackRuns = ExpandTrackRuns(simParams['trackers'], args.trackRuns)

    for aRun in trackRuns :
        print aRun


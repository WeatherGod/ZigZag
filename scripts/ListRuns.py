#!/usr/bin/env python

import fnmatch
import ZigZag.ParamUtils as ParamUtils
from ZigZag.ListRuns import MultiSims2Sims, CommonTrackRuns, ExpandTrackRuns
import os.path

def main(args) :
    simNames = args.simNames if not args.isMulti else MultiSims2Sims(args.simNames, args.directory)

    trackers = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(trackers, args.trackRuns)

    if not args.listfiles :
        for aRun in trackRuns :
            print(aRun)
    else :
        for simName in simNames :
            simParams = ParamUtils.ReadSimulationParams(os.path.join(args.directory, simName, 'simParams.conf'))
            for aRun in trackRuns :
                print os.path.join(args.directory, simName, simParams['result_file'] + '_' + aRun)


if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="List the trackruns for a simulation.")
    AddCommandParser('ListRuns', parser)
    """
    parser.add_argument("simNames", nargs='+',
                        help="List track runs done for SIMNAME. If more than one, then list all common track runs.",
                        metavar="SIMNAME")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')
    parser.add_argument("-t", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to list.  List all runs if none are given.",
                        metavar="RUN", default=None)
    parser.add_argument("-m", "--multi", dest='isMulti',
                        help="Indicate that SIMNAME(s) is actually a Multi-Sim so that we can process correctly.",
                        default=False, action='store_true')
    """
    args = parser.parse_args()

    main(args)



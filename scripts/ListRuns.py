#!/usr/bin/env python
from __future__ import print_function
import fnmatch
import ZigZag.ParamUtils as ParamUtils
from ZigZag.ListRuns import MultiSims2Sims, CommonTrackRuns, ExpandTrackRuns
import os.path

def main(args) :
    simNames = (args.simNames if not args.isMulti else
                MultiSims2Sims(args.simNames, args.directory)

    trackers = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(trackers, args.trackRuns)

    if not args.listfiles :
        for aRun in trackRuns :
            print(aRun)
    else :
        for simName in simNames :
            simParams = ParamUtils.ReadSimulationParams(
                    os.path.join(args.directory, simName, 'simParams.conf'))
            for aRun in trackRuns :
                print(os.path.join(args.directory, simName,
                      simParams['result_file'] + '_' + aRun))


if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="List the trackruns for a simulation.")
    AddCommandParser('ListRuns', parser)
    args = parser.parse_args()

    main(args)



#!/usr/bin/env python

from ZigZag.AnalyzeTracking import SingleTracking
import ZigZag.ParamUtils as ParamUtils	  # for reading simParams files
import os.path


def main(args) :
    from ZigZag.ListRuns import ExpandTrackRuns

    dirName = os.path.join(args.directory, args.simName)
    simFile = os.path.join(dirName, "simParams.conf")
    simParams = ParamUtils.ReadSimulationParams(simFile)
    
    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs)
    trackRuns = ExpandTrackRuns(trackConfs.keys(), args.trackRuns)
    trackrunConfs = dict([(runName, trackConfs[runName]) for runName in trackRuns])

    SingleTracking(simFile, args.simName, simParams, trackrunConfs, path=args.directory)



if __name__ == "__main__" :
    import argparse       # Command-line parsing
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description='Track the given centroids')
    AddCommandParser('DoTracking', parser)
    """
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')
    """

    args = parser.parse_args()

    main(args)



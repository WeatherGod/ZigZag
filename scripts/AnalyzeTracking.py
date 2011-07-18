#!/usr/bin/env python

import numpy as np
import ZigZag.ParamUtils as ParamUtils
import os.path
from ZigZag.ListRuns import ExpandTrackRuns
from ZigZag.AnalyzeTracking import AnalyzeTrackings, DisplaySkillScores



def main(args) :
    if args.cacheOnly :
        args.skillNames = []

    dirName = os.path.join(args.directory, args.simName)
    simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName, "simParams.conf"))

    # We only want to process the trackers as specified by the user
    trackRuns = ExpandTrackRuns(simParams['trackers'], args.trackRuns)

    analysis = AnalyzeTrackings(args.simName, simParams, args.skillNames,
                                trackRuns=trackRuns, path=args.directory)

    if not args.cacheOnly :
        analysis = analysis.insertaxis(axis=1, label=args.simName)
        for skill in args.skillNames :
            DisplaySkillScores(analysis.lix[[skill]], skill)
            print '\n\n'
   

if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Analyze the tracking results of a storm-track simulation")

    AddCommandParser('AnalyzeTracking', parser)
    """
    parser.add_argument("simName", type=str,
                      help="Analyze tracks for SIMNAME",
                      metavar="SIMNAME", default="NewSim")
    parser.add_argument("skillNames", nargs="+",
                        help="The skill measures to use (e.g., HSS)",
                        metavar="SKILL")
    parser.add_argument("-t", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to analyze.  Analyze all runs if none are given",
                        metavar="RUN", default=None)
    parser.add_argument("--cache", dest="cacheOnly",
                        help="Only bother with processing for the purpose of caching results.",
                        action="store_true", default=False)
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')
    """

    args = parser.parse_args()

    main(args)



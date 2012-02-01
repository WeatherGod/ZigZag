#!/usr/bin/env python

import numpy as np
import ZigZag.ParamUtils as ParamUtils
import os.path
from ZigZag.ListRuns import ExpandTrackRuns
from ZigZag.AnalyzeTracking import AnalyzeTrackings, DisplaySkillScores



def main(args) :
    dirName = os.path.join(args.directory, args.simName)
    paramFile = os.path.join(dirName, "simParams.conf")
    simParams = ParamUtils.ReadSimulationParams(paramFile)

    # We only want to process the trackers as specified by the user
    trackRuns = ExpandTrackRuns(simParams['trackers'], args.trackRuns)

    analysis = AnalyzeTrackings(args.simName, simParams, args.skillNames,
                                trackRuns=trackRuns, path=args.directory,
                                tag_filters=args.filters)

    analysis = analysis.insertaxis(axis=1, label=args.simName)
    for skill in args.skillNames :
        DisplaySkillScores(analysis.lix[[skill]], skill)
        print '\n\n'
   

if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description="Analyze the tracking results"
                                                 " of a storm-track simulation")

    AddCommandParser('AnalyzeTracking', parser)
    args = parser.parse_args()

    main(args)



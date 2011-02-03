#!/usr/bin/env python

import fnmatch
import ZigZag.ParamUtils as ParamUtils
import os

def ExpandTrackRuns(allTrackRuns, requestedRuns=None) :
    """
    Some requested runs may have glob-like search expressions.
    This resolves those expressions and returns a list of requested
    runs fully qualified.
    """
    expandedAll = []
    if requestedRuns is None :
        expandedAll.extend(allTrackRuns)
        expandedAll.sort()
    else :
        for aRun in requestedRuns :
            matches = fnmatch.filter(allTrackRuns, aRun)
            if len(matches) == 0 :
                raise ValueError("Could not find a track to match: " + aRun)
            matches.sort()
            expandedAll.extend(matches)

    return expandedAll

def CommonTrackRuns(simNames, dirName='.') :
    allTrackRuns = []

    for simName in simNames :
        simParams = ParamUtils.ReadSimulationParams(os.sep.join([dirName, simName, "simParams.conf"]))
        allTrackRuns.append(set(simParams['trackers']))

    # Get the intersection of all the sets of trackRuns in each simulation
    return list(set.intersection(*allTrackRuns))


def Sims_of_MultiSim(multiSim, dirName='.') :
    """ Build list of actual single-sim names for a multi-sim.
        Note that this does not include the multi-sim's name in the list. """
    paramFile = os.sep.join([dirName, multiSim, "MultiSim.ini"])
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    return ["%.3d" % index for index in xrange(int(multiSimParams['simCnt']))]

def MultiSims2Sims(multiSims, dirName='.') :
    """ Build list of actual single-sim names from a list of multi-sim names.
        This list includes the name of the corresponding multi-sim with the individual sims."""
    simNames = []
    for multiSim in multiSims :
        sims = Sims_of_MultiSim(multiSim, dirName)
        simNames.extend([os.sep.join([multiSim, aSim]) for aSim in sims])

    return simNames


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


    simNames = args.simNames if not args.isMulti else MultiSims2Sims(args.simNames, args.directory)

    trackers = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(trackers, args.trackRuns)

    for aRun in trackRuns :
        print aRun


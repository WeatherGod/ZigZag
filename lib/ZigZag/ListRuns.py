
import fnmatch
import ZigZag.ParamUtils as ParamUtils
import os.path

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
        simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName, simName, "simParams.conf"))
        allTrackRuns.append(set(simParams['trackers']))

    # Get the intersection of all the sets of trackRuns in each simulation
    return list(set.intersection(*allTrackRuns))


def Sims_of_MultiSim(multiSim, dirName='.') :
    """ Build list of actual single-sim names for a multi-sim.
        Note that this does not include the multi-sim's name in the list. """
    paramFile = os.path.join(dirName, multiSim, "MultiSim.ini")
    multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)
    return ["%.3d" % index for index in xrange(int(multiSimParams['simCnt']))]

def MultiSims2Sims(multiSims, dirName='.') :
    """ Build list of actual single-sim names from a list of multi-sim names.
        This list includes the name of the corresponding multi-sim with the individual sims."""
    simNames = []
    for multiSim in multiSims :
        sims = Sims_of_MultiSim(multiSim, dirName)
        simNames.extend([os.path.join(multiSim, aSim) for aSim in sims])

    return simNames


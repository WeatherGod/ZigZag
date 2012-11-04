from __future__ import print_function
import fnmatch
import ZigZag.ParamUtils as ParamUtils
import os.path
from os import rename, remove

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

def RenameRuns(simName, old, new, trackRuns, dirName='.') :
    """
    For *trackRuns* in *simName*, replace the *old* portion with *new*.

    This over-writes existing trackruns and does a bit of house-keeping
    in situations where the old run is incomplete while the existing new
    run has extra files. Also takes care of the simulation param file and
    the stored tracker configuration file, if it exists.
    """
    simDir = os.path.join(dirName, simName)
    simFile = os.path.join(simDir, "simParams.conf")
    storedConfFile = os.path.join(simDir, simParams['trackerparams'])

    simParams = ParamUtils.ReadSimulationParams(simFile)

    if not os.path.exists(storedConfFile) :
        # Initialize an empty config file
        ParamUtils.SaveConfigFile(storedConfFile, {})

    # Now load that one file
    trackerConfs = ParamUtils.LoadTrackerParams([storedConfFile])

    for oldRun in trackRuns :
        newRun = oldRun.replace(old, new)

        RenameRun(simName, simParams, trackerConfs,
                  oldRun, newRun, dirName=dirName)

        # TODO: We could use some sort of 'with' clause here to restore
        #       the original file if something goes wrong here.
        ParamUtils.SaveSimulationParams(simFile, simParams)
        ParamUtils.SaveConfigFile(storedConfFile, trackerConfs)
    


def RenameRun(simName, simParams, trackerConfs, oldRun, newRun, dirName='.') :
    """
    Renames a track run *oldRun* to *newRun*. Converts all related
    files and stored parameters as well.

    While the values in *simParams* and *trackerConfs* are updated,
    the data structures are not saved to file right away.

    Note: We strip any leading and trailing whitespaces to avoid
          issues with saving that name in config files.  Have not
          tested for names with whitespaces in them. Also, this
          precludes the naming of a track run with an empty string
          after stripping.
    """
    newRun = newRun.strip()
    if newRun == '' :
        raise ValueError("Can not convert the trackrun name to an empty string after stripping")

    if newRun == oldRun :
        print("WARNING: New run name is the same as the old. No changes will be made")
        return

    simDir = os.path.join(dirName, simName)

    oldFile = os.path.join(simDir, simParams['result_file'] + '_' + oldRun)
    newFile = os.path.join(simDir, simParams['result_file'] + '_' + newRun)
    
    # Need to check for the existance of the result file.
    if not os.path.exists(oldFile) :
        raise ValueError(
                "The track run called '%s' does not exist for Sim '%s' in directory '%s'" %
                 (oldRun, simName, dirName))

    # Rename the file...
    rename(oldFile, newFile)

    # Now check for the existance of cached result files with the old name
    # If none exists, then also check for the existance of cached result files
    # under the new name.  If those exists, then get rid of them to prevent
    # accidentially using invalid cache files.
    anyMissing = False
    for truthtable_suffix in ['_Correct.segs', '_Wrong.segs',
                              '_Correct.ind', '_Wrong.ind'] :
        oldfname = os.path.join(simDir, simParam['analysis_stem'] + "_" +
                                        oldRun + truthtable_suffix)
        newfname = os.path.join(simDir, simParam['analysis_stem'] + "_" +
                                        newRun + truthtable_suffix)
        if not os.path.exists(oldfname) :
            anyMissing = True
            continue
        
        rename(oldfname, newfname)

    if anyMissing :
        for truthtable_suffix in ['_Correct.segs', '_Wrong.segs',
                                  '_Correct.ind', '_Wrong.ind'] :
        
            newfname = os.path.join(simDir, simParam['analysis_stem'] + "_" +
                                            newRun + truthtable_suffix)
            if os.path.exists(newfname) :
                remove(newfname)


    # Also make the appropriate changes to the simParams, but it is the caller's
    # responsibility to save the params to file.
    simParam['trackers'].remove(oldRun)
    # Want to make sure we keep a sorted, unique list of track runs.
    simParam['trackers'].append(newRun)
    tempHold = list(set(simParam['trackers']))
    tempHold.sort()
    simParam['trackers'] = tempHold

    # Finally, modify the key name in the tracker confs
    if oldRun in trackerConfs :
        tempConf = trackerConfs.pop(oldRun)
        trackerConfs[newRun] = tempConf
    elif newRun in trackerConfs :
        # We don't have any info on the tracker's configs, but we
        # can't keep the existing confs around, so pop it.
        trackerConfs.pop(newRun)


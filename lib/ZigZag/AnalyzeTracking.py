import os.path
from ZigZag.TrackUtils import FilterMHTTracks, CreateSegments, MakeContingency,\
                              FilterSegments
from ZigZag.TrackFileUtils import ReadTracks
import ZigZag.Trackers as Trackers
import ZigZag.ParamUtils as ParamUtils
import numpy as np
import ZigZag.Analyzers as Analyzers
from la import larry        # Labeled arrays


# This library module contains two major sections.
# The first section is comprised of functions related
# to the analysis and display of tracking results
# The second section is comprised of functions related
# to the execution of tracking algorithms

###########################################
#     Tracking Analysis
###########################################
def DisplaySkillScores(skillScores, skillScoreName) :
    """
    Display the skill score results in a neat manner.

    Note, this function messes around with the formatting options
    of printing numpy arrays.  It does restore the settings back to
    the numpy defaults, but if you had your own formatting specified
    before calling this function, you will need to reset it.
    """

    np.set_string_function(
            lambda x: '\n'.join(['  '.join(["% 11.8f" % val for val in row])
                                                            for row in x]),
            repr=True)

    # Print the last eleven characters of each trackrun name for
    # the column labels.
    print '  '.join(["%11.11s" % tracker[-11:] for
                     tracker in skillScores.label[-1]])

    print repr(skillScores.x)

    print "-" * (11*skillScores.shape[1] + 2*(skillScores.shape[1] - 1))

    # Resetting back to how it was
    np.set_string_function(None, repr=True)



def DisplayAnalysis(analysis, skillName,
                    doFindBest=True, doFindWorst=True, compareTo=None) :
    DisplaySkillScores(analysis, skillName)

    if doFindBest or doFindWorst :
        if compareTo is None :
            compareTo = analysis.label[1][0]

        # We separate the skillscores for just the one tracker and
        # the rest of the trackers.  We use keep_label because it
        # doesn't squeeze the results down to a scalar float.
        skillscores = analysis.keep_label('==', compareTo, axis=1)
        theOthers = analysis.keep_label('!=', compareTo, axis=1)

        # Do a numpy-style subtraction (for broadcasting reasons)
        scoreDiffs = skillscores.x - theOthers.x
        # Sort score differences for each tracker 
        indices = np.argsort(scoreDiffs, axis=0)

        print "\n Against: ", '  '.join(["%7s" % tracker for
                                         tracker in theOthers.label[1]])
        if doFindBest :
            print "Best Run: ", '  '.join(["%7d" % index for
                                           index in indices[-1]])

        if doFindWorst :
            print "Worst Run:", '  '.join(["%7d" % index for
                                           index in indices[0]])

def _recurse_find(tags, name) :
    res = None

    for section in tags.sections :
        if section == name :
            return tags[section]['ids']
        else :
            res = _recurse_find(tags[section], name)
            if res is not None :
                return res

    return res

def _find_names(tags) :
    names = []
    for sect in tags.sections :
        names.extend(_find_names(tags[sect]))
    names.extend(tags.sections)

    return names

def process_tag_filters(tagFile, filters) :
    if filters is None or not os.path.exists(tagFile) :
        return None

    # Split the list into "includes" and "excludes" based on the
    # presence of a '+' or '-' sign at the end of each tagname.
    in_tags = [name[:-1] for name in filters if name[-1] == '+']
    ex_tags = [name[:-1] for name in filters if name[-1] == '-']

    keepers = set()

    simTags = ParamUtils.ReadSimTagFile(tagFile)

    if len(in_tags) == 0 :
        # Assume we mean that we want all of the generators
        in_tags = _find_names(simTags)

    for name in in_tags :
        ids = _recurse_find(simTags, name)
        if ids is None :
            raise ValueError("%s is not in the simTags file %s" %
                             (name, tagFile))
        keepers.update(ids)

    for name in ex_tags :
        ids = _recurse_find(simTags, name)
        if ids is None :
            raise ValueError("%s is not in the simTags file %s" %
                             (name, tagFile))
        keepers.difference_update(ids)

    return keepers


def AnalyzeTrackings(simName, simParams, skillNames, trackRuns, path='.',
                     tag_filters=None) :
    dirName = os.path.join(path, simName)
    trackFile = os.path.join(dirName, simParams['noisyTrackFile'])

    tagFile = os.path.join(dirName, simParams['simTagFile'])
    keeperIDs = process_tag_filters(tagFile, tag_filters)

    (true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(trackFile))
    lastFrame = (max(trk['frameNums'][-1] for trk in
                    (true_tracks + true_falarms)) if
                 len(true_tracks) + len(true_falarms) > 0 else 0)
    true_AssocSegs, trackIndices = CreateSegments(true_tracks,
                                                  retindices=True,
                                                  lastFrame=lastFrame)
    # TODO: need to filter trackIndices as well!
    true_AssocSegs = FilterSegments(keeperIDs, true_AssocSegs)

    true_FAlarmSegs, falarmIndices = CreateSegments(true_falarms,
                                                    retindices=True,
                                                    lastFrame=lastFrame)
    true_FAlarmSegs = FilterSegments(keeperIDs, true_FAlarmSegs)

    # Initializing the analysis data, which will hold a table of analysis
    # results for this simulation
    analysis = np.empty((len(skillNames),
                         len(trackRuns)))
    labels = [skillNames, trackRuns]
    
    for trackerIndex, tracker in enumerate(trackRuns) :
        obvFilename = os.path.join(dirName, simParams['result_file'] +
                                            "_" + tracker)
        (obvTracks, obvFAlarms) = FilterMHTTracks(*ReadTracks(obvFilename))
        trk_segs = CreateSegments(obvTracks + obvFAlarms, lastFrame=lastFrame)
        trk_segs = FilterSegments(keeperIDs, trk_segs)
        truthTable = MakeContingency(true_AssocSegs + true_FAlarmSegs, trk_segs)

        #print "Margin Sums: %d" % (len(truthTable['assocs_Correct']) +
        #                           len(truthTable['assocs_Wrong']) +
        #                           len(truthTable['falarms_Wrong']) +
        #                           len(truthTable['falarms_Correct']))

        for skillIndex, skill in enumerate(skillNames) :
            analysis[skillIndex,
                     trackerIndex] = Analyzers.skillcalcs[skill](
                                       tracks=obvTracks, falarms=obvFAlarms,
                                       truthTable=truthTable,
                                       true_tracks=true_tracks,
                                       true_falarms=true_falarms,
                                       track_indices=trackIndices,
                                       falarm_indices=falarmIndices)
    return larry(analysis, labels)


###########################################
#         Tracking
###########################################

def SingleTracking(simFile, simName, simParams, trackConfs, path='.') :
    #simParams['trackers'] = trackConfs.keys()
    simDir = os.path.join(path, simName, '')

    storedConfFile = os.path.join(simDir, simParams['trackerparams'])
    if not os.path.exists(storedConfFile) :
        # Initialize an empty config file
        ParamUtils.SaveConfigFile(storedConfFile, {})

    # Now load that one file
    storedTrackConfs = ParamUtils.LoadTrackerParams([storedConfFile])

    for trackRun in trackConfs :
        tracker = trackConfs[trackRun]['algorithm']
        # This is where the tracking is performed!
        # Trackers.trackerList is a dictionary of Tracker objects
        Trackers.trackerList[tracker](trackRun, simParams.copy(),
                                      trackConfs[trackRun].copy(),
                                      returnResults=False, path=simDir)

        # We want this simulation to know which trackers they used,
        # so we will update the file after each successful tracking operation.
        # Note that we still want an ordered, unique list, henced the use of
        # set() and .sort()
        simParams['trackers'].append(trackRun)
        tempHold = list(set(simParams['trackers']))
        tempHold.sort()
        simParams['trackers'] = tempHold

        # TODO: We could use some sort of 'with' clause here to restore
        #       the original file if something goes wrong here.
        ParamUtils.SaveSimulationParams(simFile, simParams)

        # Add these tracker configurations to the sim's global
        # tracker configuration file for record-keeping
        storedTrackConfs[trackRun] = trackConfs[trackRun].copy()
        ParamUtils.SaveConfigFile(storedConfFile, storedTrackConfs)



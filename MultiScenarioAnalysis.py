#!/usr/bin/env python

import MultiAnalysis as manal
import ParamUtils
import os
import numpy as np

def CommonTrackRuns_Scenarios(multiSims, dirName) :
    allTrackRuns = []

    for aMultiSim in multiSims :
        multiDir = dirName + os.sep + aMultiSim
        paramFile = multiDir + os.sep + "MultiSim.ini"
        multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)

        allTrackRuns.append(set(manal.FindCommonTrackRuns(multiSimParams['simCnt'], multiDir)))

    return list(set.intersection(*allTrackRuns))

def MultiScenarioAnalyze(multiSims, skillNames, trackRuns,
                         n_boot, ci_alpha, path='.') :

    skillMeans = np.empty((len(multiSims), len(skillNames), len(trackRuns)))
    means_ci_upper = np.empty_like(skillMeans)
    means_ci_lower = np.empty_like(skillMeans)

    for sceneIndex, aScenario in enumerate(multiSims) :
        multiDir = path + os.sep + aScenario
        paramFile = multiDir + os.sep + "MultiSim.ini"
        multiSimParams = ParamUtils.Read_MultiSim_Params(paramFile)

        analysis = manal.MultiAnalyze(multiSimParams, skillNames,
                                      trackRuns, path=path)

        for skillIndex, skillName in enumerate(skillNames) :
            btmean, btci = manal.Bootstrapping(n_boot, ci_alpha, analysis.lix[[skillName]].x)
            skillMeans[sceneIndex, skillIndex, :] = btmean
            means_ci_upper[sceneIndex, skillIndex, :] = btci[0]
            means_ci_lower[sceneIndex, skillIndex, :] = btci[1]

    return skillMeans, means_ci_upper, means_ci_lower


if __name__ == '__main__' :
    import argparse
    from ListRuns import ExpandTrackRuns
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description='Analyze the tracking results of multiple scenarios of multiple storm-track simulations')
    parser.add_argument("multiSims",
                      help="Analyze tracks for MULTISIM",
                      nargs='+',
                      metavar="MULTISIM", type=str)
    parser.add_argument("-s", "--skills", dest="skillNames",
                        help="The skill measures to use",
                        nargs='+', metavar="SKILL")
    parser.add_argument("-t", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to analyze.  Analyze all common runs if none are given",
                        metavar="RUN", default=None)
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM",
                        metavar="DIRNAME", default='.')

    args = parser.parse_args()

    n_boot = 100
    ci_alpha = 0.05

    if len(args.multiSims) < 2 :
        raise ValueError("Need at least 2 scenarios to analyze")

    commonTrackRuns = CommonTrackRuns_Scenarios(args.multiSims, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    # If there was any expansion, then we probably want to sort these.
    # The idea being that if the user specified which trackers to use, then
    # he probably wants it in the order that he gave it in, otherwise sort it.
    if (args.trackRuns is not None) and (len(args.trackRuns) != len(trackRuns)) :
        trackRuns.sort()

    meanSkills, skills_ci_upper, skills_ci_lower = MultiScenarioAnalyze(args.multiSims, args.skillNames, trackRuns,
                                                                        n_boot, ci_alpha, path=args.directory)

    figs = [None] * len(args.skillNames)
    for sceneIndex, aScene in enumerate(args.multiSims) :
        for skillIndex, skillName in enumerate(args.skillNames) :
            if figs[skillIndex] is None :
                figs[skillIndex] = plt.figure()

            ax = figs[skillIndex].add_subplot(111)

            manal.MakeErrorBars(meanSkills[sceneIndex, skillIndex, :],
                                (skills_ci_upper[sceneIndex, skillIndex, :],
                                 skills_ci_lower[sceneIndex, skillIndex, :]),
                                trackRuns, ax, sceneIndex)

    for aFig in figs :
        ax = aFig.add_subplot(111)
        ax.set_xticks(np.arange(len(args.multiSims)) + 0.5)
        ax.set_xticklabels(args.multiSims)
        ax.set_xlim((0.0, len(args.multiSims)))

    plt.show()

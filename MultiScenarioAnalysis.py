#!/usr/bin/env python

import MultiAnalysis as manal
import ParamUtils
import os
import numpy as np
from ListRuns import Sims_of_MultiSim
import matplotlib.pyplot as plt

def MultiScenarioAnalyze(multiSims, skillNames, trackRuns,
                         n_boot, ci_alpha, path='.') :

    skillMeans = np.empty((len(multiSims), len(skillNames), len(trackRuns)))
    means_ci_upper = np.empty_like(skillMeans)
    means_ci_lower = np.empty_like(skillMeans)

    for sceneIndex, aScenario in enumerate(multiSims) :
        simNames = Sims_of_MultiSim(aScenario, path)
        analysis = manal.MultiAnalyze(simNames, aScenario, skillNames,
                                      trackRuns, path=path)

        for skillIndex, skillName in enumerate(skillNames) :
            btmean, btci = manal.Bootstrapping(n_boot, ci_alpha, analysis.lix[[skillName]].x)
            skillMeans[sceneIndex, skillIndex, :] = btmean
            means_ci_upper[sceneIndex, skillIndex, :] = btci[0]
            means_ci_lower[sceneIndex, skillIndex, :] = btci[1]

    return skillMeans, means_ci_upper, means_ci_lower

def DisplayMultiSceneAnalysis(skillNames, shortNames, multiSims, 
                              meanSkills, skills_ci_upper, skills_ci_lower,
                              figsize=None) :
    figs = [None] * len(skillNames)
    for runIndex, trackRun in enumerate(shortNames) :
        for skillIndex, skillName in enumerate(skillNames) :
            if figs[skillIndex] is None :
                figs[skillIndex] = plt.figure(figsize=figsize)

            ax = figs[skillIndex].gca()

            manal.MakeErrorBars(meanSkills[:, skillIndex, runIndex],
                                (skills_ci_upper[:, skillIndex, runIndex],
                                 skills_ci_lower[:, skillIndex, runIndex]),
                                ax, startLoc=(runIndex + 1)/(len(shortNames) + 1.0),
                                label=trackRun)

    for figIndex, aFig in enumerate(figs) :
        ax = aFig.gca()
        ax.set_xticks(np.arange(len(multiSims)) + 0.5)
        ax.set_xticklabels(multiSims)
        ax.set_xlim((0.0, len(multiSims)))
        ax.set_title(skillNames[figIndex])
        ax.legend(numpoints=1, loc='lower left', bbox_to_anchor=(0.95, 0.9))

    return figs


if __name__ == '__main__' :
    import argparse
    from ListRuns import ExpandTrackRuns, CommonTrackRuns, MultiSims2Sims


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
    parser.add_argument("--cache", dest="cacheOnly",
                        help="Only bother with processing for the purpose of caching results.",
                        action="store_true", default=False)
    parser.add_argument("--save", dest="saveImgFile", type=str,
                        help="Save the resulting image using FILESTEM as the prefix. (e.g., saved file will be 'foo/bar_PC.png' for the PC skill scores and suffix of 'foo/bar').  Use --type to control which image format.",
                        metavar="FILESTEM", default=None)
    parser.add_argument("--type", dest="imageType", type=str,
                        help="Image format to use for saving the figures. Default: %(default)s",
                        metavar="TYPE", default='png')
    parser.add_argument("-f", "--figsize", dest="figsize", type=float,
                        nargs=2, help="Size of the figure in inches (width x height). Default: %(default)s",
                        metavar="SIZE", default=(11.0, 5.0))
    parser.add_argument("--noshow", dest="doShow", action = 'store_false',
                        help="To display or not to display...",
                        default=True)
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM",
                        metavar="DIRNAME", default='.')

    args = parser.parse_args()

    n_boot = 100
    ci_alpha = 0.05

    if len(args.multiSims) < 2 :
        raise ValueError("Need at least 2 scenarios to analyze")

    if args.cacheOnly :
        args.skillNames = []


    simNames = MultiSims2Sims(args.multiSims, args.directory)
    commonTrackRuns = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    meanSkills, skills_ci_upper, skills_ci_lower = MultiScenarioAnalyze(args.multiSims, args.skillNames, trackRuns,
                                                                        n_boot, ci_alpha, path=args.directory)

    if not args.cacheOnly :
        shortNames = [runname[-11:] for runname in trackRuns]

        figs = DisplayMultiSceneAnalysis(args.skillNames, shortNames, args.multiSims,
                                         meanSkills, skills_ci_upper, skills_ci_lower,
                                         figsize=args.figsize)

        if args.saveImgFile is not None :
            for aFig, skillName in zip(figs, args.skillNames) :
                aFig.savefig("%s_%s.%s" % (args.saveImgFile, skillName, args.imageType))

        if args.doShow :
            plt.show()

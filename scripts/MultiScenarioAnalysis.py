#!/usr/bin/env python

from ZigZag.AnalyzeTracking import DisplayAnalysis, AnalyzeTrackings
from ZigZag.AnalysisPlot import MakeErrorBars
import ZigZag.ParamUtils as ParamUtils
import os.path
import numpy as np
from ZigZag.ListRuns import CommonTrackRuns, Sims_of_MultiSim
import ZigZag.bootstrap as btstrp

from multiprocessing import Pool

def MultiScenarioAnalyze(multiSims, skillNames, trackRuns,
                         n_boot, ci_alpha, path='.') :

    skillMeans = np.empty((len(multiSims), len(skillNames), len(trackRuns)))
    means_ci_upper = np.empty_like(skillMeans)
    means_ci_lower = np.empty_like(skillMeans)

    for sceneIndex, aScenario in enumerate(multiSims) :
        simNames = Sims_of_MultiSim(aScenario, path)
        analysis = MultiAnalyze(simNames, aScenario, skillNames,
                                trackRuns, path=path)

        for skillIndex, skillName in enumerate(skillNames) :
            btmean, btci = Bootstrapping(n_boot, ci_alpha, analysis.lix[[skillName]].x)
            skillMeans[sceneIndex, skillIndex, :] = btmean
            means_ci_upper[sceneIndex, skillIndex, :] = btci[0]
            means_ci_lower[sceneIndex, skillIndex, :] = btci[1]

    return skillMeans, means_ci_upper, means_ci_lower


def _analyze_trackings(simName, multiSim, skillNames, trackRuns, multiDir) :
    try :
        dirName = os.path.join(multiDir, simName)
        paramFile = os.path.join(dirName, "simParams.conf")
        print "Sim:", simName
        simParams = ParamUtils.ReadSimulationParams(paramFile)

        analysis = AnalyzeTrackings(simName, simParams, skillNames,
                                    trackRuns=trackRuns, path=multiDir)
        analysis = analysis.insertaxis(axis=1, label=simName)
    except Exception as err :
        print err
        raise err
    return analysis


def MultiAnalyze(simNames, multiSim, skillNames,
                 trackRuns, path='.') :
    completeAnalysis = None
    multiDir = os.path.join(path, multiSim)

    p = Pool()

    # Now, go through each simulation and analyze them.
    results = [p.apply_async(_analyze_trackings, (simName, multiSim, skillNames,
                                                  trackRuns, multiDir)) for
               simName in simNames]

    p.close()
    p.join()

    # FIXME: With the update larrys, this can probably be improved.
    for res in results :
        if completeAnalysis is None :
            completeAnalysis = res.get()
        else :
            completeAnalysis = completeAnalysis.merge(res.get())

    return completeAnalysis

def Bootstrapping(n_boot, ci_alpha, analysisInfo) :
    booting = btstrp.bootstrap(n_boot, np.mean, analysisInfo, axis=0)
    btmean = booting.mean(axis=0)
    btci = btstrp.bootci(n_boot, np.mean, analysisInfo, alpha=ci_alpha, axis=0)

    return btmean, btci



def DisplayMultiSceneAnalysis(figTitles, runLabels, tickLabels,
                              meanSkills, skills_ci_upper, skills_ci_lower,
                              figs) :

    for runIndex, trackRun in enumerate(runLabels) :
        for skillIndex in range(len(figTitles)) :
            ax = figs[skillIndex].gca()

            MakeErrorBars(meanSkills[:, skillIndex, runIndex],
                          (skills_ci_upper[:, skillIndex, runIndex],
                           skills_ci_lower[:, skillIndex, runIndex]),
                          ax, startLoc=(runIndex + 1)/(len(runLabels) + 1.0),
                          label=trackRun)

    for aFig, title in zip(figs, figTitles) :
        ax = aFig.gca()
        ax.set_xticks(np.arange(len(tickLabels)) + 0.5)
        ax.set_xticklabels(tickLabels)
        ax.set_xlim((0.0, len(tickLabels)))
        ax.set_ylabel("Skill Score")
        ax.set_title(title)
        # We want the upper-right corner of the legend to be
        # in the figure's upper right corner.
        ax.legend(numpoints=1, loc='upper right',
                  bbox_transform=aFig.transFigure,
                  bbox_to_anchor=(0.99, 0.99))

def main(args) :
    from ZigZag.ListRuns import ExpandTrackRuns, CommonTrackRuns, \
                                MultiSims2Sims

    n_boot = 100
    ci_alpha = 0.05

    if len(args.multiSims) < 2 :
        raise ValueError("Need at least 2 scenarios to analyze")

    if args.cacheOnly :
        args.skillNames = []
    else :
        import matplotlib.pyplot as plt



    simNames = MultiSims2Sims(args.multiSims, args.directory)
    commonTrackRuns = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    (meanSkills,
     skills_ci_upper,
     skills_ci_lower) = MultiScenarioAnalyze(args.multiSims, args.skillNames,
                                             trackRuns, n_boot, ci_alpha,
                                             path=args.directory)

    if not args.cacheOnly :
        tickLabels = args.ticklabels if args.ticklabels is not None else args.multiSims
        figTitles = args.titles if args.titles is not None else args.skillNames
        plotLabels = args.plotlabels if args.plotlabels is not None else trackRuns

        figs = [plt.figure(figsize=args.figsize) for title in figTitles]
        DisplayMultiSceneAnalysis(figTitles, plotLabels, tickLabels,
                                  meanSkills, skills_ci_upper, skills_ci_lower,
                                  figs)


        for aFig, skillName in zip(figs, args.skillNames) :
            if args.saveImgFile is not None :
                aFig.savefig("%s_%s.%s" % (args.saveImgFile, skillName, args.imageType))

        if args.doShow :
            plt.show()


if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser



    parser = argparse.ArgumentParser(description='Analyze the tracking results of multiple scenarios of multiple storm-track simulations')
    AddCommandParser('MultiScenarioAnalysis', parser)
    """
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
    """
    args = parser.parse_args()

    main(args)



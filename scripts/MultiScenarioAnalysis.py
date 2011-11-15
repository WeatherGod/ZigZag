#!/usr/bin/env python

from ZigZag.AnalyzeTracking import DisplayAnalysis, AnalyzeTrackings
from ZigZag.AnalysisPlot import MakeErrorBars
import ZigZag.ParamUtils as ParamUtils
import os.path
import numpy as np
import la
from ZigZag.ListRuns import CommonTrackRuns, Sims_of_MultiSim
import ZigZag.bootstrap as btstrp

from multiprocessing import Pool

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



def MultiScenarioAnalyze(multiSims, skillNames, trackRuns,
                         n_boot, ci_alpha, path='.') :

    skillMeans = np.empty((len(multiSims), len(skillNames), len(trackRuns)))
    means_ci_upper = np.empty_like(skillMeans)
    means_ci_lower = np.empty_like(skillMeans)

    for sceneIndex, aScenario in enumerate(multiSims) :
        simNames = Sims_of_MultiSim(aScenario, path)
        # (Skills x Sims x TrackRuns)
        analysis = MultiAnalyze(simNames, aScenario, skillNames,
                                trackRuns, path=path)

        # Perform averages over the simulations for each skillscore
        for skillIndex, skillName in enumerate(skillNames) :
            btmean, btci = Bootstrapping(n_boot, ci_alpha, analysis.lix[[skillName]].x)
            skillMeans[sceneIndex, skillIndex, :] = btmean
            means_ci_upper[sceneIndex, skillIndex, :] = btci[0]
            means_ci_lower[sceneIndex, skillIndex, :] = btci[1]

    return skillMeans, means_ci_upper, means_ci_lower


def Bootstrapping(n_boot, ci_alpha, analysisInfo) :
    booting = btstrp.bootstrap(n_boot, np.mean, analysisInfo, axis=0)
    btmean = booting.mean(axis=0)
    btci = btstrp.bootci(n_boot, np.mean, analysisInfo, alpha=ci_alpha, axis=0)

    return btmean, btci


_dispFmt = {'cat' : '.',
            'ordinal' : '-'}


def DisplayMultiSceneAnalysis(figTitles, plotLabels, tickLabels,
                              meanSkills, skills_ci_upper, skills_ci_lower,
                              figs, dispMode='cat') :
    """
    Display the error bars for the skill scores.

    *dispMode*  ['cat' | 'ordinal']
        Categorical or ordinal mode for the x-axis
    """
    fmt = _dispFmt[dispMode]

    for plotIndex, label in enumerate(plotLabels) :
        startLoc = 0.5 if dispMode == 'ordinal' else \
                   ((plotIndex + 1) / (len(plotLabels) + 1.0))

        for figIndex in range(len(figTitles)) :
            ax = figs[figIndex].gca()

            MakeErrorBars(meanSkills[:, figIndex, plotIndex],
                          (skills_ci_upper[:, figIndex, plotIndex],
                           skills_ci_lower[:, figIndex, plotIndex]),
                          ax, startLoc=startLoc, label=label,
                          fmt=fmt)

    leg_objs = []

    for aFig, title in zip(figs, figTitles) :
        ax = aFig.gca()
        ax.set_xticks(np.arange(len(tickLabels)) + 0.5)
        ax.set_xticklabels(tickLabels)
        ax.set_xlim((0.0, len(tickLabels)))
        ax.set_ylabel("Skill Score")
        ax.set_title(title)
        # We want the upper-right corner of the legend to be
        # in the figure's upper right corner.
        leg = ax.legend(numpoints=1, loc='upper left',
                        #bbox_transform=aFig.transFigure,
                        bbox_to_anchor=(1.01, 1.01))
        leg_objs.append(leg)

    return leg_objs

def Rearrange(display, *args) :
    # Now we need to roll data axes around so that it matches with what the
    # user wants to display.
    dataAxes = {'scenarios' : 0,
                'skills'    : 1,
                'trackruns' : 2}

    args = list(args)

    increm = 0
    # Only need to roll twice, as the last will fall into place
    for destAxis, dispName in enumerate(['ticks', 'fig']) :
        srcAxis = (dataAxes[display[dispName]] + increm) % len(dataAxes)
        for index in range(len(args)) :
            args[index] = np.rollaxis(args[index], srcAxis, destAxis)
        if (srcAxis - destAxis) > 1 :
            # other items had to shift, so we need to increment
            increm += 1

    return args

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

    # Validate the command-line arguments for display options
    if (set(['skills', 'trackruns', 'scenarios']) !=
        set([args.fig_disp, args.plot_disp, args.tick_disp])) :
        raise ValueError("The '--fig', '--plot', and '--tick' options must each be unique: [fig: %s, plot: %s, tick: %s)" %
                         (args.fig_disp, args.plot_disp, args.tick_disp))


    simNames = MultiSims2Sims(args.multiSims, args.directory)
    commonTrackRuns = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    # meanSkills, and the ci's are 3D (scenarios x skills x trackruns)
    (meanSkills,
     skills_ci_upper,
     skills_ci_lower) = MultiScenarioAnalyze(args.multiSims, args.skillNames,
                                             trackRuns, n_boot, ci_alpha,
                                             path=args.directory)
    if not args.cacheOnly :
        display = {disp:data for disp, data in
                    zip(['fig', 'plot', 'ticks'],
                        [args.fig_disp, args.plot_disp, args.tick_disp])}

        defaultLabels = {'skills' : args.skillNames,
                         'trackruns' : trackRuns,
                         'scenarios' : args.multiSims}

        (meanSkills,
         skills_ci_upper,
         skills_ci_lower) = Rearrange(display, meanSkills, skills_ci_upper,
                                                           skills_ci_lower)
        


        tickLabels = args.ticklabels if args.ticklabels is not None else \
                     defaultLabels[display['ticks']]
        figTitles = args.titles if args.titles is not None else \
                    defaultLabels[display['fig']]
        plotLabels = args.plotlabels if args.plotlabels is not None else \
                     defaultLabels[display['plot']]

        figs = [plt.figure(figsize=args.figsize) for title in figTitles]
        legs = DisplayMultiSceneAnalysis(figTitles, plotLabels, tickLabels,
                                  meanSkills, skills_ci_upper, skills_ci_lower,
                                  figs, dispMode=args.dispMode)


        for aFig, legend, title in zip(figs, legs,
                                       defaultLabels[display['fig']]) :
            aFig.gca().set_xlabel(args.xlabel)
            if args.saveImgFile is not None :
                aFig.savefig("%s_%s.%s" % (args.saveImgFile,
                                           title, args.imageType),
                             bbox_inches='tight', pad_inches=0.25,
                             bbox_extra_artists=[legend])

        if args.doShow :
            plt.show()


if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser



    parser = argparse.ArgumentParser(description='Analyze the tracking results of multiple scenarios of multiple storm-track simulations')
    AddCommandParser('MultiScenarioAnalysis', parser)
    parser.add_argument("--mode", dest="dispMode",
                        help="Mode for x-axis (categorical (default) or ordinal). In categorical mode, error bars are unconnected and non-overlapping. In ordinal mode, the errorbars for each plot are connected, and are overlapping in the x-axis.",
                        choices=['cat', 'ordinal'], default='cat')
    parser.add_argument("--xlabel", dest="xlabel", type=str,
                        help="Label for the x-axis.  Default: '%(default)s'",
                        default='')
    parser.add_argument("--fig", dest="fig_disp", type=str,
                        help="Figures should be organized by... %(choices)s (Default: %(default)s)",
                        choices=['skills', 'trackruns', 'scenarios'],
                        default='skills')
    parser.add_argument("--plot", dest="plot_disp", type=str,
                        help="Plot errorbars by... %(choices)s (Default: %(default)s)",
                        choices=['skills', 'trackruns', 'scenarios'],
                        default='trackruns')
    parser.add_argument("--tick", dest="tick_disp", type=str,
                        help="Values for the x-axis are from... %(choices)s (Default: %(default)s)",
                        choices=['skills', 'trackruns', 'scenarios'],
                        default='scenarios')
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



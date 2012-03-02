#!/usr/bin/env python

from ZigZag.AnalyzeTracking import DisplayAnalysis, AnalyzeTrackings
from ZigZag.AnalysisPlot import MakeErrorBars
import ZigZag.ParamUtils as ParamUtils
import os.path
import numpy as np
import la
from ZigZag.ListRuns import CommonTrackRuns, Sims_of_MultiSim
import ZigZag.bootstrap as btstrp
import matplotlib.pyplot as plt

from multiprocessing import Pool

def _analyze_trackings(simName, multiSim, skillNames, trackRuns, multiDir,
                       tag_filters) :
    try :
        dirName = os.path.join(multiDir, simName)
        paramFile = os.path.join(dirName, "simParams.conf")
        print "Sim:", simName
        simParams = ParamUtils.ReadSimulationParams(paramFile)
        tagFile = os.path.join(dirName, simParams['simTagFile'])

        if os.path.exists(tagFile) :
            simTags = ParamUtils.ReadConfigFile(tagFile)
        else :
            simTags = None

        analysis = AnalyzeTrackings(simName, simParams, skillNames,
                                    trackRuns=trackRuns, path=multiDir,
                                    tag_filters=tag_filters)
        analysis = analysis.insertaxis(axis=1, label=simName)
    except Exception as err :
        print err
        raise err
    return analysis


def MultiAnalyze(simNames, multiSim, skillNames,
                 trackRuns, path='.', tag_filters=None) :
    completeAnalysis = None
    multiDir = os.path.join(path, multiSim)

    p = Pool()

    # Now, go through each simulation and analyze them.
    results = [p.apply_async(_analyze_trackings, (simName, multiSim, skillNames,
                                                  trackRuns, multiDir,
                                                  tag_filters)) for
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
                         n_boot, ci_alpha, path='.', tag_filters=None) :

    skillMeans = np.empty((len(multiSims), len(skillNames), len(trackRuns)))
    means_ci_upper = np.empty_like(skillMeans)
    means_ci_lower = np.empty_like(skillMeans)

    for sceneIndex, aScenario in enumerate(multiSims) :
        simNames = Sims_of_MultiSim(aScenario, path)
        # (Skills x Sims x TrackRuns)
        analysis = MultiAnalyze(simNames, aScenario, skillNames,
                                trackRuns, path=path, tag_filters=tag_filters)

        # Perform averages over the simulations for each skillscore
        for skillIndex, skillName in enumerate(skillNames) :
            btmean, btci = Bootstrapping(n_boot, ci_alpha,
                                         analysis.lix[[skillName]].x)
            skillMeans[sceneIndex, skillIndex, :] = btmean
            means_ci_upper[sceneIndex, skillIndex, :] = btci[0]
            means_ci_lower[sceneIndex, skillIndex, :] = btci[1]

    return skillMeans, means_ci_upper, means_ci_lower


def Bootstrapping(n_boot, ci_alpha, analysisInfo) :
    booting = btstrp.bootstrap(n_boot, np.mean, analysisInfo, axis=0)
    btmean = booting.mean(axis=0)
    btci = btstrp.bootci(n_boot, np.mean, analysisInfo, alpha=ci_alpha, axis=0)

    return btmean, btci


_dispFmt = {'cat' : '.',}
#            'ordinal' : '-'}

_graphTypes = {'cat' : 'line',
               'ordinal' : 'line',
               'bar' : 'bar'}


def DisplayMultiSceneAnalysis(figTitles, plotLabels, tickLabels,
                              meanSkills, skills_ci_upper, skills_ci_lower,
                              figs, dispMode='cat') :
    """
    Display the error bars for the skill scores.

    *dispMode*  ['cat' (default) | 'ordinal', 'bar']
        Categorical or ordinal mode for the x-axis
    """
    extra_kwargs = {}

    if dispMode in _dispFmt :
        # Some modes don't require a "format".
        extra_kwargs['fmt'] = _dispFmt[dispMode]

    # But all modes require a graph type
    graphType = _graphTypes[dispMode]

    leg_objs = []
    extra_kwargs['width'] = 1.0 / (len(plotLabels) + 1.0)

    for figIndex, (fig, title) in enumerate(zip(figs, figTitles)) :
        ax = figs[figIndex].gca()

        for plotIndex, label in enumerate(plotLabels) :
            startLoc = 0.5 if dispMode == 'ordinal' else \
                       ((plotIndex + 1) * extra_kwargs['width'])

            MakeErrorBars(meanSkills[:, figIndex, plotIndex],
                          (skills_ci_upper[:, figIndex, plotIndex],
                           skills_ci_lower[:, figIndex, plotIndex]),
                          ax, startLoc=startLoc, label=label,
                          graphType=graphType, **extra_kwargs)

        if dispMode == 'bar' :
            ax.set_ylim(ymin=skills_ci_lower[:, figIndex, :].min() * 0.95)

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

def DisplayTableAnalysis(figTitles, plotLabels, tickLabels,
                         meanSkills, skills_ci_upper, skills_ci_lower) :
    np.set_string_function(
            lambda x: '  '.join(["% 8.4f" % val for val in x]),
            repr=True)

    for figIndex, title in enumerate(figTitles) :
        print "%50s" % title

        print " " * 10,
        print " ".join(["%9s"] * len(tickLabels)) % tuple(tickLabels)
        print "-" * (11 + 10 * len(tickLabels))

        for plotIndex, label in enumerate(plotLabels) :
            print ("%10s|" % label),
            print repr(meanSkills[:, figIndex, plotIndex])


    # Restore the formatting state to the default
    np.set_string_function(None, repr=True)

dataAxes = {'scenarios' : 0,
            'skills'    : 1,
            'trackruns' : 2}

def Rearrange(display, *args) :
    # Now we need to roll data axes around so that it matches with what the
    # user wants to display.
    # Convert a tuple into a list
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

def _varval(x, varname) :
    y = x.split('_')
    return y[y.index(varname) + 1]

def _remove_varval(x, varname) :
    "Assumes that *x* has already been split"
    y = x.index(varname)
    # Now remove that element
    x.pop(y)
    # And remove its value (note that there is one less, so the value is
    # at the same location as its name was a moment ago.
    x.pop(y)
    return x

def Regroup(groupinfo, labels, *args) :
    """
    Modify the 3D numpy arrays in *args so that data is grouped
    according to user specifications.

    For example, presume that the following scenarios are given:

    Fast_Down_01
    Slow_Down_01
    Fast_Down_02
    Slow_Down_02
    Fast_Down_04
    Slow_Down_04
    Fast_Down_08
    Slow_Down_08

    And only a single track run is specified: SCIT.
    In this example, the third item, skill scores, can be arbitrary.
    Now, supposed that we want to display the result data such that the x-axis
    is for the Down* and there are two plots: one for Fast and one for Slow.

    So, we group the scenarios data by some key (discussed later) _into_
    the trackruns dimension. For this reason, the data dimension being
    grouped into (in this case, trackruns) must originally be singleton.

    *groupinfo* - dict with keys "group", "into", and "by".
        The "group" element states which dimension the grouping will occur on.
        The "into" element states along which dimension the groups will be
        stacked. These two elements can have values of "scenarios", "skills",
        or "trackruns".

        The "by" element is rudimentary for now, but it controls the key value
        function used for grouping. The key function is applied to the list of
        default labels for the dimension stated for "group". The unique set of
        keys generated by the function on these labels become the new default
        labels for the "into" dimension.

        Currently, the keyfunction is hard-coded to split the label by under-
        scores and search for the string given in "by" in the resulting list.
        It then returns the list's next value. So, in the above example, the
        new labels for the "trackruns" dimension would be "01", "02", "04", and
        "08".
    """
    if groupinfo is None :
        return args

    if len(args) == 0 :
        return args

    if len(labels[groupinfo['into']]) != 1 :
        raise ValueError("Dim %s is not singleton!" % groupinfo['into'])

    if groupinfo['group'] == groupinfo['into'] :
        raise ValueError("Can not group %s dimension into itself!" %
                         groupinfo['group'])

    from pandas import Panel

    grpAxis = dataAxes[groupinfo['group']]
    intoAxis = dataAxes[groupinfo['into']]
    otherAxis = dataAxes[list(set(['scenarios', 'trackruns', 'skills']) -
                              set([groupinfo['group'], groupinfo['into']]))[0]]

    # !!Temporary!! restricted functionality for just trackrun variables
    keyfunc = lambda x : _varval(x, groupinfo['by'])

    g_args = []
    for a in args :
        wp = Panel(a, items=labels['scenarios'],
                      major_axis=labels['skills'],
                      minor_axis=labels['trackruns'])

        grouped = wp.groupby(keyfunc, axis=grpAxis)

        if len(grouped) == 0 :
            raise ValueError("Grouping didn't result in anything!")

        intolabs, g_a = zip(*grouped)
        # Get a list of numpy arrays from the list of Panels
        g_a = np.concatenate(map(lambda x : x.values, g_a),
                             axis=intoAxis)

        g_args.append(g_a)

    labels[groupinfo['into']] = intolabs

    # Do the full set for error-checking purposes
    trunclabs = None
    for intolab in intolabs :
        # TODO: Generalize this!
        # Take some original labels and remove the variable and its value that
        # were used to make *intolabs*
        tmp = ['_'.join(_remove_varval(lab.split('_'), groupinfo['by'])) for
               lab in grouped.groups[intolab]]
        if trunclabs is not None :
            if tmp != trunclabs :
                raise ValueError("The labels do not match! %s\n%s" %
                                 (trunclabs, tmp))
        else :
            trunclabs = tmp

    labels[groupinfo['group']] = trunclabs

    return g_args



def main(args) :
    from ZigZag.ListRuns import ExpandTrackRuns, CommonTrackRuns, \
                                MultiSims2Sims

    n_boot = 100
    ci_alpha = 0.05

    #if len(args.multiSims) < 2 :
    #    raise ValueError("Need at least 2 scenarios to analyze")

    if args.groupby is not None :
        # Perform substitution of the 'group' option with the 'into' value
        # from --group
        if args.fig_disp == 'group' :
            args.fig_disp = args.groupby[1]
        if args.plot_disp == 'group' :
            args.plot_disp = args.groupby[1]
        if args.tick_disp == 'group' :
            args.tick_disp = args.groupby[1]

    if args.bw_mode :
        colors = ['0.25', '0.75', '0.5']
        if args.dispMode == 'bar' :
            # Make the last one white
            colors.append('1.0')
        else :
            # Make the last one black
            colors.append('0.0')

        plt.rcParams['axes.color_cycle'] = colors

    # These are experimental features in matplotlib and may not
    # exist in the user's installation.
    if 'style.cycle' in plt.rcParams :
        plt.rcParams['style.cycle'] = True
    if 'cycle.hatch' in plt.rcParams :
        plt.rcParams['cycle.hatch'] = True

    # Validate the command-line arguments for display options
    if (set(['skills', 'trackruns', 'scenarios']) !=
        set([args.fig_disp, args.plot_disp, args.tick_disp])) :
        raise ValueError("The '--fig', '--plot', and '--tick' options"
                         " must each be unique:"
                         " [fig: %s, plot: %s, tick: %s)" %
                         (args.fig_disp, args.plot_disp, args.tick_disp))


    simNames = MultiSims2Sims(args.multiSims, args.directory)
    commonTrackRuns = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    # meanSkills, and the ci's are 3D (scenarios x skills x trackruns)
    (meanSkills,
     skills_ci_upper,
     skills_ci_lower) = MultiScenarioAnalyze(args.multiSims, args.skillNames,
                                             trackRuns, n_boot, ci_alpha,
                                             tag_filters=args.filters,
                                             path=args.directory)
    display = {disp:data for disp, data in
               zip(['fig', 'plot', 'ticks'],
                   [args.fig_disp, args.plot_disp, args.tick_disp])}

    defaultLabels = {'skills' : args.skillNames,
                     'trackruns' : trackRuns,
                     'scenarios' : args.multiSims}

    groupinfo = (None if args.groupby is None else
                 dict(group=args.groupby[0],
                      into=args.groupby[1],
                      by=args.groupby[2]))

    #groupinfo = {'group' : 'trackruns',
    #             'into' : 'scenarios',
    #             'by' : 'framesBack'}

    # Default labels may be modified by Regroup()
    (meanSkills,
     skills_ci_upper,
     skills_ci_lower) = Regroup(groupinfo, defaultLabels, meanSkills,
                                                          skills_ci_upper,
                                                          skills_ci_lower)

    #print meanSkills.shape
    #print len(defaultLabels['scenarios']), len(defaultLabels['skills']),\
    #      len(defaultLabels['trackruns'])

    (meanSkills,
     skills_ci_upper,
     skills_ci_lower) = Rearrange(display, meanSkills,
                                           skills_ci_upper,
                                           skills_ci_lower)

    #print meanSkills.shape

    tickLabels = args.ticklabels if args.ticklabels is not None else \
                 defaultLabels[display['ticks']]
    figTitles = args.titles if args.titles is not None else \
                defaultLabels[display['fig']]
    plotLabels = args.plotlabels if args.plotlabels is not None else \
                 defaultLabels[display['plot']]

    #print len(tickLabels), len(figTitles), len(plotLabels)

    figs = [plt.figure(figsize=args.figsize) for title in figTitles]
    legs = DisplayMultiSceneAnalysis(figTitles, plotLabels, tickLabels,
                              meanSkills, skills_ci_upper, skills_ci_lower,
                              figs, dispMode=args.dispMode)

    if args.showTables :
        DisplayTableAnalysis(figTitles, plotLabels, tickLabels,
                             meanSkills, skills_ci_upper, skills_ci_lower)


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

    parser = argparse.ArgumentParser(description='Analyze the tracking results'
                                            ' of multiple scenarios of'
                                            ' multiple storm-track simulations')
    AddCommandParser('MultiScenarioAnalysis', parser)
    parser.add_argument("--mode", dest="dispMode",
                        help="Mode for x-axis (categorical (default),"
                             " ordinal, or bar). In categorical mode, error"
                             " bars are unconnected and non-overlapping. In"
                             " ordinal  mode, the errorbars for each plot are"
                             " connected, and are overlapping in the x-axis."
                             " For bar, bars are used with errorbars.",
                        choices=['cat', 'ordinal', 'bar'], default='cat')
    parser.add_argument("--tables", dest="showTables", action='store_true',
                        help="Output tabulated results",
                        default=False)
    parser.add_argument("--xlabel", dest="xlabel", type=str,
                        help="Label for the x-axis.  Default: '%(default)s'",
                        default='')
    parser.add_argument("--fig", dest="fig_disp", type=str,
                        help="Figures should be organized by... %(choices)s."
                             " The 'group' option is a convenience option"
                             " that can be used when --group is used."
                             " (Default: %(default)s)",
                        choices=['skills', 'trackruns', 'scenarios', 'group'],
                        default='skills')
    parser.add_argument("--plot", dest="plot_disp", type=str,
                        help="Plot errorbars by... %(choices)s."
                             " The 'group' option is a convenience option"
                             " that can be used when --group is used."
                             " (Default: %(default)s)",
                        choices=['skills', 'trackruns', 'scenarios', 'group'],
                        default='trackruns')
    parser.add_argument("--tick", dest="tick_disp", type=str,
                        help="Values for the x-axis are from... %(choices)s."
                             " The 'group' option is a convenience option"
                             " that can be used when --group is used."
                             " (Default: %(default)s)",
                        choices=['skills', 'trackruns', 'scenarios', 'group'],
                        default='scenarios')
    parser.add_argument("--group", dest="groupby", type=str, nargs=3,
                        help="Perform a 'groupby' of the data. The three"
                             " arguments represent (1) the dimension to group,"
                             " (2) the dimension to split the data into,"
                             " and (3) the key by which to group (1)'s"
                             " dimensions.",
                        metavar="GROUP", default=None)
    args = parser.parse_args()

    main(args)



#!/usr/bin/env python

from MultiScenarioAnalysis import DisplayAnalysis, \
                                  Bootstrapping
from ZigZag.AnalyzeTracking import MultiAnalyze
from ZigZag.AnalysisPlot import MakeErrorBars
import ZigZag.ParamUtils as ParamUtils
import os.path
import numpy as np
import matplotlib.pyplot as plt

def main(args) :
    from ZigZag.ListRuns import ExpandTrackRuns, Sims_of_MultiSim, CommonTrackRuns

    n_boot = 1000
    ci_alpha = 0.05

    if args.bw_mode :
        colors = ['0.25', '0.75', '0.5', '0.0']
        plt.rcParams['axes.color_cycle'] = colors

    if 'style.cycle' in plt.rcParams :
        # This is an experimental feature in matplotlib, and may not
        # exist in the user's installation
        plt.rcParams['style.cycle'] = True

    simNames = Sims_of_MultiSim(args.multiSim, args.directory)
    fullNames = [os.path.join(args.multiSim, aSim) for aSim in simNames]
    commonTrackRuns = CommonTrackRuns(fullNames, args.directory)
    trackRuns = ExpandTrackRuns(commonTrackRuns, args.trackRuns)

    shortNames = args.ticklabels if args.ticklabels is not None else \
                        [runname[-11:] for runname in trackRuns]
    plotTitles = args.titles if args.titles is not None else args.skillNames

    completeAnalysis = MultiAnalyze(simNames, args.multiSim, args.skillNames,
                                    trackRuns=trackRuns, path=args.directory)

    for skillname, title in zip(args.skillNames, plotTitles) :
        DisplayAnalysis(completeAnalysis.lix[[skillname]], skillname,
                        args.doFindBest, args.doFindWorst,
                        compareTo=args.compareTo)
        print "\n\n"

        btmean, btci = Bootstrapping(n_boot, ci_alpha, completeAnalysis.lix[[skillname]].x)

        fig = plt.figure(figsize=args.figsize)
        ax = fig.gca()
        
        MakeErrorBars(btmean, btci, ax)
        ax.set_xticks(np.arange(len(btmean)) + 0.5)
        ax.set_xticklabels(shortNames, fontsize='medium')
        ax.set_xlim(0.0, len(shortNames))
        #ax.set_xlabel(xlab)
        ax.set_ylabel('Skill Score')
        ax.set_title(title)

        if args.saveImgFile is not None :
            fig.savefig("%s_%s.%s" % (args.saveImgFile, skillname, args.imageType))

    if args.doShow:
        plt.show()


if __name__ == "__main__" :
    import argparse     # Command-line parsing
    from ZigZag.zigargs import AddCommandParser

    parser = argparse.ArgumentParser(description='Analyze the tracking results of multiple storm-track simulations')
    AddCommandParser('MultiAnalysis', parser)
    args = parser.parse_args()

    main(args)



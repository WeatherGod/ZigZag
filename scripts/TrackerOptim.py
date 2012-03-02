#!/usr/bin/env python

import os.path
import ZigZag.Trackers as Trackers
import ZigZag.ParamUtils as ParamUtils     # for reading simParams files

from ZigZag.ListRuns import Sims_of_MultiSim
from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks, CreateSegments, \
                              MakeContingency
import ZigZag.Analyzers as Analyzers

import numpy as np

from multiprocessing import Pool

def _track_and_analyze(simName, true_segs, lastFrame,
                       tracker, trackConfs, multiDir) :
    try :
        paramFile = os.path.join(multiDir, simName, "simParams.conf")
        simParams = ParamUtils.ReadSimulationParams(paramFile)

        (obv_tracks,
         obv_falarms) = Trackers.trackerList[tracker]("__optim__",
                                                      simParams, trackConfs,
                                        path=os.path.join(multiDir, simName))

        trk_segs = CreateSegments(obv_tracks + obv_falarms, lastFrame=lastFrame)

        truthTable = MakeContingency(true_segs, trk_segs)
        return 100.0 - Analyzers.skillcalcs['PC'](truthTable=truthTable)
    except Exception as err :
        print err
        raise

from scipy.optimize import fmin

def TrackOpt(multiSim, trackConfs, path='.') :
    simNames = Sims_of_MultiSim(multiSim, path)
    multiDir = os.path.join(path, multiSim)

    segs = []
    lastFrames = []
    for simName in simNames :
        paramFile = os.path.join(multiDir, simName, "simParams.conf")
        simParams = ParamUtils.ReadSimulationParams(paramFile)
        trackFile = os.path.join(multiDir, simName, simParams['noisyTrackFile'])
        true_tracks, true_falarms = FilterMHTTracks(*ReadTracks(trackFile))
        lastFrame = (max(trk['frameNums'][-1] for trk in
                         (true_tracks + true_falarms)) if
                         len(true_tracks) + len(true_falarms) > 0 else 0)
        true_Segs = CreateSegments(true_tracks + true_falarms,
                                   retindices=False,
                                   lastFrame=lastFrame)
        # TODO: Filtering segments
        segs.append(true_Segs)
        lastFrames.append(lastFrame)

    # TODO: Make this better!
    trackrun = trackConfs.keys()[0]

    otherParams = dict()
    x0 = []
    paramNames = []

    for param, x in trackConfs[trackrun].iteritems() :
        if isinstance(x, str) :
            otherParams[param] = x
        else :
            x0.append(float(x))
            paramNames.append(param)
    res = fmin(_track_and_analyze_wrap, x0, (paramNames,
                                             simNames, segs, lastFrames,
                                             trackrun,
                                             otherParams, multiDir),
               xtol=0.01, ftol=0.1)

    return res



def _track_and_analyze_wrap(x, paramNames,
                            simNames, segs, lastFrames,
                            trackrun, otherParams, multiDir) :
    trackConfs = {param:val for param, val in zip(paramNames, x)}
    trackConfs.update(otherParams)
    p = Pool()

    results = [p.apply_async(_track_and_analyze,
                             (simName, true_segs, lastFrame,
                              trackrun, trackConfs.copy(),
                              multiDir)) for (simName, true_segs, lastFrame) in
               zip(simNames, segs, lastFrames)]

    p.close()
    p.join()

    return np.mean([res.get() for res in results])


def main(args) :
    from ZigZag.ListRuns import ExpandTrackRuns
    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs)

    trackRuns = ExpandTrackRuns(trackConfs.keys(), args.trackRuns)
    
    trackrunConfs = dict([(runName, trackConfs[runName]) for runName in trackRuns])

    trackparams = TrackOpt(args.multiSim, trackrunConfs, path=args.directory)

    print trackparams



if __name__ == '__main__' :
    import argparse       # Command-line parsing
    from ZigZag.zigargs import AddCommandParser



    parser = argparse.ArgumentParser(description='Search for optimal params'
                                                 ' for your tracker.')

    AddCommandParser("MultiTracking", parser)
    args = parser.parse_args()

    main(args)



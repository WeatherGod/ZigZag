#!/usr/bin/env python

import os.path
import ZigZag.Trackers as Trackers
from DoTracking import SingleTracking
import ZigZag.ParamUtils as ParamUtils     # for reading simParams files

from ListRuns import Sims_of_MultiSim

from multiprocessing import Pool

def _prepare_and_track(simName, trackConfs, multiDir) :
    print "Sim:", simName
    paramFile = os.path.join(multiDir, simName, "simParams.conf")
    simParams = ParamUtils.ReadSimulationParams(paramFile)

    SingleTracking(paramFile, simName, simParams, trackConfs, path=multiDir)

def MultiTrack(multiSim, trackConfs, path='.') :
    simNames = Sims_of_MultiSim(multiSim, path)
    multiDir = os.path.join(path, multiSim)

    p = Pool()

    for simName in simNames :
        # A copy of trackConfs is used here because the tracker calls could
        # modify the contents of trackConfs, and we don't want those changes
        # to propagate to subsequent calls to SingleTracking()
        p.apply_async(_prepare_and_track, (simName, trackConfs.copy(), multiDir))

    p.close()
    p.join()


def main(args) :
    from ListRuns import ExpandTrackRuns
    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs)

    trackRuns = ExpandTrackRuns(trackConfs.keys(), args.trackRuns)
    
    trackrunConfs = dict([(runName, trackConfs[runName]) for runName in trackRuns])
    
    MultiTrack(args.multiSim, trackrunConfs, path=args.directory)



if __name__ == '__main__' :
    import argparse       # Command-line parsing
    from ZigZag.zigargs import AddCommandParser



    parser = argparse.ArgumentParser(description='Track the given centroids')

    AddCommandParser("MultiTracking", parser)
    """
    parser.add_argument("multiSim",
                      help="Generate Tracks for MULTISIM",
                      metavar="MULTISIM")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-t", "--trackruns", dest="trackRuns",
                        nargs="+", help="Trackruns to perform.  Perform all runs in CONF if none are given.",
                        metavar="RUN", default=None)
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find MULTISIM",
                        metavar="DIRNAME", default='.')
    """

    args = parser.parse_args()

    main(args)



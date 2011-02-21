#!/usr/bin/env python

import ZigZag.Trackers as Trackers
import ZigZag.ParamUtils as ParamUtils	  # for reading simParams files
import os.path


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
        Trackers.trackerList[tracker](trackRun, simParams.copy(), trackConfs[trackRun].copy(),
                                      returnResults=False, path=simDir)

        # We want this simulation to know which trackers they used,
        # so we will update the file after each successful tracking operation.
        # Note that we still want an ordered, unique list, henced the use of
        # set() and .sort()
        simParams['trackers'].append(trackRun)
        tempHold = list(set(simParams['trackers']))
        tempHold.sort()
        simParams['trackers'] = tempHold
        ParamUtils.SaveSimulationParams(simFile, simParams)

        storedTrackConfs[trackRun] = trackConfs[trackRun].copy()
        ParamUtils.SaveConfigFile(storedConfFile, storedTrackConfs)

def main(args) :
    from ListRuns import ExpandTrackRuns

    dirName = os.path.join(args.directory, args.simName)
    simFile = os.path.join(dirName, "simParams.conf")
    simParams = ParamUtils.ReadSimulationParams(simFile)
    
    trackConfs = ParamUtils.LoadTrackerParams(args.trackconfs)
    trackRuns = ExpandTrackRuns(trackConfs.keys(), args.trackRuns)
    trackrunConfs = dict([(runName, trackConfs[runName]) for runName in trackRuns])

    SingleTracking(simFile, args.simName, simParams, trackrunConfs, path=args.directory)



if __name__ == "__main__" :
    import argparse       # Command-line parsing
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description='Track the given centroids')
    AddCommandParser('DoTracking', parser)
    """
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME",
                      metavar="SIMNAME")
    parser.add_argument("trackconfs", nargs='+',
                      help="Config files for the parameters for the trackers",
                      metavar="CONF")
    parser.add_argument("-d", "--dir", dest="directory",
                        help="Base directory to find SIMNAME",
                        metavar="DIRNAME", default='.')
    """

    args = parser.parse_args()

    main(args)



#!/usr/bin/env python

import ParamUtils
import Trackers

import os                               # for os.sep.join(), os.system()

if __name__ == "__main__" :
    import ParamUtils	  # for reading simParams files
    import argparse       # Command-line parsing
    parser = argparse.ArgumentParser(description='Track the given centroids')
    parser.add_argument("simName",
                      help="Generate Tracks for SIMNAME (default: %(default)s)",
                      metavar="SIMNAME", default="NewSim")
    parser.add_argument("trackers", nargs='+',
                        help="TRACKER to use for tracking the centroids",
                        metavar="TRACKER", choices=['SCIT', 'MHT'], default='SCIT')
    args = parser.parse_args()

    simParams = ParamUtils.ReadSimulationParams(os.sep.join([args.simName, "simParams.conf"]))

    simParams['ParamFile'] = os.sep.join([args.simName, "Parameters"])
    
    for tracker in args.trackers :
        Trackers.trackerList[tracker](simParams, returnResults=False)



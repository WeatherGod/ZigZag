#!/usr/bin/env python

from DoTracking import DoTracking
#import ParamUtils

import os			# for os.sep, os.system()


if __name__ == "__main__" :
    import argparse	     # Command-line parsing
    
    parser = argparse.ArgumentParser(description="The Test Track...")
    parser.add_argument("inputFileName", nargs=1,
                        help="Input data file")
    parser.add_argument("paramFileName", nargs=1,
                        help="MHT Parameter Filename")
    parser.add_argument("-p", "--path", dest="pathName",
		      help = "PATHNAME for corner files", metavar="PATHNAME",
		      default = ".")
    parser.add_argument("-t", "--tracker", dest="trackers", type=str,
		      action="append",
		      help="Tracking algorithms to use. (Ex: MHT)",
		      metavar="TRACKER", default=['SCIT'])
    
    args = parser.parse_args()


    trackParams = {'ParamFile': args.paramFileName, 'inputDataFile': args.inputFileName,
		   'result_file': args.pathName + os.sep + 'testResults'}

    for aTracker in args.trackers :
	DoTracking(aTracker, trackParams, returnResults)


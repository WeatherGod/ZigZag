#!/usr/bin/env python
import optparse			# for command-line parsing

from DoTracking import DoTracking
#import ParamUtils

import os			# for os.sep, os.system()


if __name__ == "__main__" :
    from optparse import OptionParser     # Command-line parsing
    
    parser = OptionParser()
    parser.add_option("-p", "--path", dest = "pathName",
		      help = "PATHNAME for corner files", metavar = "PATHNAME",
		      default = ".")
    parser.add_option("-t", "--tracker", dest = "trackers", type = "string",
		      action = "append",
		      help = "Tracking algorithms to use, in addition to SCIT. (Ex: MHT)",
		      metavar="TRACKER", default = ['SCIT'])
    
    (options, args) = parser.parse_args()

    print "ARGS: ", args
    if len(args) != 2 : print "ERROR: The input data file and the MHT param file are needed!"
    
    inputFileName = args[0]
    paramFileName = args[1]

    trackParams = {'ParamFile': paramFileName, 'inputDataFile': inputFileName,
		   'result_file': options.pathName + os.sep + 'testResults'}

    for aTracker in options.trackers :
	DoTracking(aTracker, trackParams, returnResults)


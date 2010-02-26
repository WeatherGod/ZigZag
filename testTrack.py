#!/usr/bin/env python
import optparse			# for command-line parsing

from DoTracking import DoTracking
from TrackFileUtils import ReadCorners

import os			# for os.sep, os.system()


if __name__ == "__main__" :
    from optparse import OptionParser     # Command-line parsing
    
    parser = OptionParser()
    parser.add_option("-p", "--path", dest = "pathName",
		      help = "PATHNAME for corner files", metavar = "PATHNAME",
		      default = ".")
    
    (options, args) = parser.parse_args()

    print "ARGS: ", args
    if len(args) != 2 : print "ERROR: The input data file and the MHT param file are needed!"
    
    inputFileName = args[0]
    paramFileName = args[1]

    trackParams = {'ParamFile': paramFileName, 'inputDataFile': inputFileName,
		   'result_filestem': options.pathName + os.sep + 'testResults'}

    (mhtTracks, mhtFAs) = DoTracking('MHT', trackParams, returnResults = True)
    (scitTracks, scitFAs) = DoTracking('SCIT', trackParams, returnResults = True)



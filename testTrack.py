#!/usr/bin/env python
import optparse			# for command-line parsing

from DoTracking import DoTracking
from TrackFileUtils import ReadCorners
from TrackPlot import PlotTrack
from TrackUtils import DomainFromTracks

import pylab
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

    print len(mhtTracks), len(mhtFAs), len(scitTracks), len(scitFAs)

    #theDomain = DomainFromTracks(mhtTracks, mhtFAs)
    theDomain = [ [-250.0, 20.0], [-20.0, 250.0], [0, 24] ]
    
    theFig = pylab.figure()
    ax = theFig.add_subplot(1, 2, 1)
    ax.hold(True)
    PlotTrack(mhtTracks, theDomain[0], theDomain[1], theDomain[2], axis = ax,
	      marker = '.', markersize = 6.0, color = 'k', linewidth = 1.5)
    PlotTrack(mhtFAs, theDomain[0], theDomain[1], theDomain[2], axis = ax,
	      marker = '.', markersize = 6.0, linestyle = ' ', color = 'k')
    ax.set_title("MHT")

    ax = theFig.add_subplot(1, 2, 2)
    ax.hold(True)
    PlotTrack(scitTracks, theDomain[0], theDomain[1], theDomain[2], axis = ax,
              marker = '.', markersize = 6.0, color = 'k', linewidth = 1.5)
    ax.set_title("SCIT")

    pylab.show()


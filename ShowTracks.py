#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()

from optparse import OptionParser	# Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing

parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")

(options, args) = parser.parse_args()


outputResults = os.sep.join([options.simName, "testResults"])
trackFile_scit = outputResults + "_SCIT"
simTrackFile = os.sep.join([options.simName, "noise_tracks"])


fileList = glob.glob(outputResults + "_MHT" + "*")

if len(fileList) == 0 : print "WARNING: No files found for '" + outputResults + "_MHT" + "'"
fileList.sort()

(true_tracks, true_falarms) = ReadTracks(simTrackFile)
(finalmhtTracks, mhtFAlarms) = ReadTracks(fileList.pop(0))
(finalmhtTracks, mhtFAlarms) = FilterMHTTracks(finalmhtTracks, mhtFAlarms)
(xLims, yLims, tLims) = DomainFromTracks(true_tracks['tracks'])

true_segs = CreateSegments(true_tracks['tracks'], true_falarms)
mht_segs = CreateSegments(finalmhtTracks, mhtFAlarms)


truthtable_mht = CompareSegments(true_segs, true_falarms, mht_segs, mhtFAlarms)


pylab.subplot(121)

#PlotSegments(truthtable_mht, xLims, yLims, tLims)
Animate_Segments(truthtable_mht, xLims, yLims, tLims, speed = 0.1, hold_loop = 2.0)

pylab.title("MHT")

"""
PlotTracks(true_tracks['tracks'], finalmhtTracks, xLims, yLims, tLims)
pylab.title('MHT  t = %d' % (max(tLims)))
pylab.savefig('MHT_Tracks.png')
pylab.clf()


for (index, trackFile_MHT) in enumerate(fileList) :
#for index in range(min(tLims), max(tLims) + 1) :
    (raw_tracks, falseAlarms) = ReadTracks(trackFile_MHT)
    mhtTracks = FilterMHTTracks(raw_tracks)

    PlotTracks(true_tracks['tracks'], mhtTracks, xLims, yLims, (min(tLims), index + 1))
    pylab.title('MHT  t = %d' % (index + 1))
    pylab.savefig('MHT_Tracks_%.2d.png' % (index + 1))
    pylab.clf()
"""

(scitTracks, scitFAlarms) = ReadTracks(trackFile_scit)
scit_segs = CreateSegments(scitTracks['tracks'], scitFAlarms)

compareResults_scit = CompareSegments(true_segs, true_falarms, scit_segs, scitFAlarms)

pylab.subplot(122)

# Correct Stuff
PlotSegment(compareResults_scit['assocs_Correct'], xLims, yLims, tLims, 
	     linewidth=1.5, color= 'green', marker='.', markersize=7.0)
PlotSegment(compareResults_scit['falarms_Correct'], xLims, yLims, tLims,
	     color='green', marker='.', linestyle=' ', markersize=7.0)

# Wrong Stuff
PlotSegment(compareResults_scit['falarms_Wrong'], xLims, yLims, tLims,
	     linewidth=1.5, color='gray', marker='.', markersize=8.0, linestyle=':')
PlotSegment(compareResults_scit['assocs_Wrong'], xLims, yLims, tLims, 
	     linewidth=1.5, color='red', marker='.', markersize=8.0)

pylab.title("SCIT")

pylab.show()

"""
for index in range(min(tLims), max(tLims) + 1) :
    PlotTracks(true_tracks['tracks'], scitTracks['tracks'], xLims, yLims, (min(tLims), index))
    pylab.title('SCIT  t = %d' % (index))
    pylab.savefig('SCIT_Tracks_%.2d.png' % (index))
    pylab.clf()

"""

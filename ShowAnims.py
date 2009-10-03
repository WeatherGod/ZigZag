#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
from ParamUtils import *                # for ReadSimulationParams()

from optparse import OptionParser	# Command-line parsing
import os				# for os.sep.join()
import glob				# for globbing
import pylab

parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")

(options, args) = parser.parse_args()

if options.simName == "" :
    options.simName = "NewSim"


fontsize = 18

simParams = ReadSimulationParams(options.simName + os.sep + "simParams.conf")

trackFile_scit = simParams['result_filestem'] + "_SCIT"
trackFile_mht = simParams['result_filestem'] + "_MHT"
simTrackFile = simParams['noisyTrackFile']

"""
fileList = glob.glob(outputResults + "_MHT" + "*")

if len(fileList) == 0 : print "WARNING: No files found for '" + outputResults + "_MHT" + "'"
fileList.sort()
"""
(true_tracks, true_falarms) = FilterMHTTracks(*ReadTracks(simParams['noisyTrackFile']))
(finalmhtTracks, mhtFAlarms) = FilterMHTTracks(*ReadTracks(trackFile_mht))
#(finalmhtTracks, mhtFAlarms) = FilterMHTTracks(finalmhtTracks, mhtFAlarms)


true_AssocSegs = CreateSegments(true_tracks)
true_FAlarmSegs = CreateSegments(true_falarms)
mht_AssocSegs = CreateSegments(finalmhtTracks)
mht_FAlarmSegs = CreateSegments(mhtFAlarms)


truthtable_mht = CompareSegments(true_AssocSegs, true_FAlarmSegs,
				 mht_AssocSegs, mht_FAlarmSegs)

# TODO: Dependent on the fact that I am doing a comparison between 2 trackers
pylab.figure(figsize=(12, 6))
curAxis = pylab.subplot(122)

#PlotSegments(truthtable_mht, simParams['xLims'], simParams['yLims'], simParams['tLims'])
Animate_Segments(truthtable_mht, simParams['xLims'], simParams['yLims'], simParams['tLims'], axis = curAxis, speed = 0.1, hold_loop = 3.0)

pylab.axis("equal")
pylab.title("MHT", fontsize=fontsize)
pylab.xlabel("X [km]")
pylab.ylabel("Y [km]")

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


(scitTracks, scitFAlarms) = FilterMHTTracks(*ReadTracks(trackFile_scit))

scit_AssocSegs = CreateSegments(scitTracks)
scit_FAlarmSegs = CreateSegments(scitFAlarms)
compareResults_scit = CompareSegments(true_AssocSegs, true_FAlarmSegs,
				      scit_AssocSegs, scit_FAlarmSegs)

# TODO: Again, assumes a comparison between two trackers
curAxis = pylab.subplot(121)

PlotSegments(compareResults_scit, simParams['xLims'], simParams['yLims'], simParams['tLims'], axis = curAxis)
pylab.axis("equal")
pylab.title("SCIT", fontsize=fontsize)
pylab.xlabel("X [km]")
pylab.ylabel("Y [km]")



"""
for index in range(min(tLims), max(tLims) + 1) :
    PlotTracks(true_tracks['tracks'], scitTracks['tracks'], xLims, yLims, (min(tLims), index))
    pylab.title('SCIT  t = %d' % (index))
    pylab.savefig('SCIT_Tracks_%.2d.png' % (index))
    pylab.clf()

"""

pylab.show()

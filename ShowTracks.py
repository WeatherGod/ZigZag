#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files

import glob

outputResults = "testyResults"
trackFile_scit = outputResults + "_SCIT"
simTrackFile = "true_tracks"


fileList = glob.glob(outputResults + "_MHT" + "*")

if len(fileList) == 0 : print "WARNING: No files found for '" + outputStemName + "_MHT" + "'"
fileList.sort()

(true_tracks, true_falarms) = ReadTracks(simTrackFile)
(finalmhtTracks, mhtAlarms) = ReadTracks(fileList.pop(0))
finalmhtTracks = FilterMHTTracks(finalmhtTracks)
(xLims, yLims, tLims) = DomainFromTracks(finalmhtTracks)

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


(scitTracks, scitFalarms) = ReadTracks(trackFile_scit)

for index in range(min(tLims), max(tLims) + 1) :
    PlotTracks(true_tracks['tracks'], scitTracks['tracks'], xLims, yLims, (min(tLims), index))
    pylab.title('SCIT  t = %d' % (index))
    pylab.savefig('SCIT_Tracks_%.2d.png' % (index))
    pylab.clf()



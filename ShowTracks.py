#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files

import glob

simTrackFile = "truetracks"
outputStemName = "testtracks_"

fileList = glob.glob(outputStemName + "*")

if len(fileList) == 0 : print "WARNING: No files found for '" + outputStemName + "'"
fileList.sort()

(true_tracks, true_falarms) = ReadTracks(simTrackFile)
(xLims, yLims) = DomainFromTracks(true_tracks)


for (index, trackFile) in enumerate(fileList) :
    (raw_tracks, falseAlarms) = ReadTracks(trackFile)
    mhtTracks = FilterMHTTracks(raw_tracks)

    PlotTracks(true_tracks, mhtTracks)
    pylab.xlim(xLims)
    pylab.ylim(yLims)
    pylab.title('MHT  t = %d' % index)
    pylab.savefig('MHT_Tracks_%.2d.png' % index)
    pylab.clf()



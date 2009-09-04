#!/usr/bin/env python

from TrackPlot import *			# for plotting tracks
from TrackFileUtils import *		# for reading track files

import glob


def CreateSegments(tracks) :
    lineSegs = {'xLocs': [], 'yLocs': [], 'frameNums': []}
    for aTrack in tracks :
	if len(aTrack['frameNums']) > 1 :
            for index2 in range(1, len(aTrack['frameNums'])) :
                index1 = index2 - 1
                lineSegs['xLocs'].append([aTrack['xLocs'][index1], aTrack['xLocs'][index2]])
                lineSegs['yLocs'].append([aTrack['yLocs'][index1], aTrack['yLocs'][index2]])
                lineSegs['frameNums'].append([aTrack['frameNums'][index1], aTrack['frameNums'][index2]])


    return lineSegs






outputResults = "testyResults"
trackFile_scit = outputResults + "_SCIT"
simTrackFile = "true_tracks"

xLims = [0, 255]
yLims = [0, 255]
tLims = [1, 9]

fileList = glob.glob(outputResults + "_MHT" + "*")

if len(fileList) == 0 : print "WARNING: No files found for '" + outputResults + "_MHT" + "'"
fileList.sort()

(true_tracks, true_falarms) = ReadTracks(simTrackFile)
#(finalmhtTracks, mhtAlarms) = ReadTracks(fileList.pop(0))
(finalmhtTracks, mhtAlarms) = ReadTracks("testyResults_MHT")
finalmhtTracks = FilterMHTTracks(finalmhtTracks)
#(xLims, yLims, tLims) = DomainFromTracks(finalmhtTracks)

true_segs = CreateSegments(true_tracks['tracks'])
mht_segs = CreateSegments(finalmhtTracks)

pylab.figure()
PlotSegments(true_segs, xLims, yLims, tLims, color= 'k', marker='.', markersize=8.0)
pylab.figure()
PlotSegments(mht_segs, xLims, yLims, tLims, color='r', marker=',', markersize=7.0, alpha = 0.6)

pylab.show()

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


(scitTracks, scitFalarms) = ReadTracks(trackFile_scit)

for index in range(min(tLims), max(tLims) + 1) :
    PlotTracks(true_tracks['tracks'], scitTracks['tracks'], xLims, yLims, (min(tLims), index))
    pylab.title('SCIT  t = %d' % (index))
    pylab.savefig('SCIT_Tracks_%.2d.png' % (index))
    pylab.clf()

"""

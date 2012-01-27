#!/usr/bin/env python

from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks, CreateSegments, DomainFromTracks
import numpy as np
from itertools import chain

from collections import defaultdict
import matplotlib.pyplot as plt

def main(args) :
    for afile in args.trackfiles :
        tracks, falarms = FilterMHTTracks(*ReadTracks(afile))
        trackSegs, trkIndices = CreateSegments(tracks, retindices=True)

        flatDists_x = np.array([np.diff(aSeg['xLocs']) for aSeg in trackSegs if
                                len(aSeg) > 1])
        flatDists_y = np.array([np.diff(aSeg['yLocs']) for aSeg in trackSegs if
                                len(aSeg) > 1])
        flatDists = np.hypot(flatDists_x, flatDists_y)

        flatdeltaFrames = np.array([np.diff(aSeg['frameNums']) for
                                    aSeg in trackSegs if len(aSeg) > 1])
        flatspeeds = flatDists / flatdeltaFrames

        dists = defaultdict(float)
        lens = defaultdict(int)
        for segDist, segDelta, trkIndex in zip(flatDists, flatdeltaFrames,
                                               trkIndices) :
            dists[trkIndex] += segDist
            lens[trkIndex] += segDelta

        trkDensity = defaultdict(int)
        for seg in trackSegs :
            trkDensity[seg['frameNums'][0]] += 1


        falrmDensity = defaultdict(int)
        for seg in falarms :
            falrmDensity[seg['frameNums'][0]] += 1

        # Convert to a list
        dists = [dists[trkIndex] for trkIndex in xrange(len(tracks))]
        lens = [lens[trkIndex] for trkIndex in xrange(len(tracks))]

        startFrames = [np.min(aTrack['frameNums']) for aTrack in tracks]
        startDensity = defaultdict(int)
        for f in startFrames :
            startDensity[f] += 1

        endFrames = [np.max(aTrack['frameNums']) for aTrack in tracks]
        endDensity = defaultdict(int)
        for f in endFrames :
            endDensity[f] += 1

        startXs = [aTrack['xLocs'][0] for aTrack in tracks]
        startYs = [aTrack['yLocs'][0] for aTrack in tracks]
        endXs = [aTrack['xLocs'][-1] for aTrack in tracks]
        endYs = [aTrack['yLocs'][-1] for aTrack in tracks]
        devs = [np.std(np.hypot(np.diff(trk['xLocs']) /
                                np.diff(trk['frameNums']),
                                np.diff(trk['yLocs']) /
                                np.diff(trk['frameNums']))) for
                trk in tracks if len(trk) > 2]

        xLims, yLims, fLims = DomainFromTracks(tracks, falarms)

        frames = np.arange(fLims[0], fLims[1] + 1)
        trkDensity = [trkDensity[frame] for frame in frames]
        falrmDensity = [falrmDensity[frame] for frame in frames]
        startDensity = [startDensity[frame] for frame in frames]
        endDensity = [endDensity[frame] for frame in frames]

        plt.figure()
        plt.plot(frames, trkDensity, label='tracks')
        plt.plot(frames, falrmDensity, label="falarms")
        plt.plot(frames, startDensity, '--', label="starts")
        plt.plot(frames, endDensity, '--', label="ends")
        plt.legend()
        
        plt.xlabel('Frame Index')
        plt.ylabel('# of detections')

        print
        print afile, ':'
        print "Track Cnt: %4d" % len(tracks)
        print "False Alarm Cnt: %4d" % len(falarms)
        print "Track SegCnt:", len(trackSegs)
        print "Limits: X", xLims, "  Y", yLims, "  Frames", fLims

        print
        print "Max  Length: %4d Frames, %8.3f" % (np.max(lens),
                                                     np.max(dists))
        print "Mean Length: %4d Frames, %8.3f" % (np.mean(lens),
                                                     np.mean(dists))
        print "Median Len : %4d Frames, %8.3f" % (np.median(lens),
                                                     np.median(dists))
        print "Min  Length: %4d Frames, %8.3f" % (np.min(lens),
                                                     np.min(dists))
        print
        print "Max  StdDev: %8.3f" % np.max(devs)
        print "Mean StdDev: %8.3f" % np.mean(devs)
        print "Median  Dev: %8.3f" % np.median(devs)
        print "Min  StdDev: %8.3f" % np.min(devs)
        print
        for name, func in zip(["Max   ", "Mean  ", "Median", "Min   "],
                              [np.max, np.mean, np.median, np.min]) :
            print name, ("Start: X %8.3f  Y %8.3f  Frame %4d" %
                         (func(startXs), func(startYs), func(startFrames)))
            print ("         End: X %8.3f  Y %8.3f  Frame %4d" %
                         (func(endXs),   func(endYs),   func(endFrames)))

        print
        print "Max  Frame-to-Frame Dist: %4d Frames, %8.3f" % \
                                (np.max(flatdeltaFrames), np.max(flatDists))
        print "Mean Frame-to-Frame Dist: %4d Frames, %8.3f" % \
                                (np.mean(flatdeltaFrames), np.mean(flatDists))
        print "Med  Frame-to-Frame Dist: %4d Frames, %8.3f" % \
                                (np.median(flatdeltaFrames),
                                 np.median(flatDists))
        print "Min  Frame-to-Frame Dist: %4d Frames, %8.3f" % \
                                (np.min(flatdeltaFrames),
                                 np.min(flatDists))
        print "Speed:", flatspeeds.min(), flatspeeds.mean(), flatspeeds.max()

    plt.show()


if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Report on each given"
                                                 " trackfile.")
    AddCommandParser('TrackReports', parser)
    args = parser.parse_args()

    main(args)



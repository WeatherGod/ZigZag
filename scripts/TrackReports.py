#!/usr/bin/env python

from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks
import numpy as np


def main(args) :

    for afile in args.trackfiles :
        tracks, falarms = FilterMHTTracks(*ReadTracks(afile))
        trackSegs = [np.diff((aTrack['xLocs'], aTrack['yLocs'])) for aTrack in tracks]
        flatSegs = []
        for segs in trackSegs :
            flatSegs.extend(segs.T)
        flatSegs = np.array(flatSegs).T
        flatDists = np.hypot(*flatSegs)
        flatWeights = flatDists / flatDists.max()

        dists = [np.sum(np.hypot(*np.diff(segs))) for segs in trackSegs]
        lens = [np.ptp(aTrack['frameNums']) + 1 for aTrack in tracks]
        startFrames = [np.min(aTrack['frameNums']) for aTrack in tracks]
        endFrames = [np.max(aTrack['frameNums']) for aTrack in tracks]

        import matplotlib.pyplot as plt
        plt.scatter(lens, dists)
        plt.xlabel('Frame Cnt')
        plt.ylabel('Distance')
        plt.xlim(min(lens), max(lens))
        plt.ylim(min(dists), max(dists))

        print
        print afile, ':'
        print "Track Cnt: %4d" % len(tracks)
        print "False Alarm Cnt: %4d" % len(falarms)
        #print "Clutter Points (estimated): %4d" % len([dist for dist, frameCnt in zip(dists, lens) if (dist < (0.5*np.mean(dists)) and frameCnt > np.mean(lens))])

        print "Max  Length: %4d Frames, %8.3f km" % (np.max(lens), np.max(dists))
        print "Mean Length: %4d Frames, %8.3f km" % (np.mean(lens), np.mean(dists))
        print "Median Len : %4d Frames, %8.3f km" % (np.median(lens), np.median(dists))
        print "Min  Length: %4d Frames, %8.3f km" % (np.min(lens), np.min(dists))

        print "Mean   Start: Frame %4d    End: Frame %4d" % (np.mean(startFrames), np.mean(endFrames))
        print "Median Start: Frame %4d    End: Frame %4d" % (np.median(startFrames), np.median(endFrames))

        print "Weighted Mean Bearing: %6.2f degrees" % np.rad2deg(np.arctan2(np.sum(flatWeights * flatSegs[0]),
                                                                             np.sum(flatWeights * flatSegs[1])))

        plt.show()
        
        
        

if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Report on each given trackfile.")
    AddCommandParser('TrackReports', parser)

    args = parser.parse_args()

    main(args)



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
#        directions = [np.arctan2(np.sum(segs[1]/np.hypot(*segs))/len(segs),
#                                 np.sum(segs[0]/np.hypot(*segs))/len(segs))
#                      for segs in trackSegs]

        print
        print afile, ':'
        print "Track Cnt: %4d" % len(tracks)
        print "False Alarm Cnt: %4d" % len(falarms)

        print "Max  Length: %4d Frames, %8.3f km" % (np.max(lens), np.max(dists))
        print "Mean Length: %4d Frames, %8.3f km" % (np.mean(lens), np.mean(dists))
        print "Min  Length: %4d Frames, %8.3f km" % (np.min(lens), np.min(dists))

        print "Weighted Mean Bearing: %6.2f degrees" % np.rad2deg(np.arctan2(np.sum(flatWeights * flatSegs[0]),
                                                                             np.sum(flatWeights * flatSegs[1])))
        
        
        

if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Report on each given trackfile.")
    AddCommandParser('TrackReports', parser)

    args = parser.parse_args()

    main(args)



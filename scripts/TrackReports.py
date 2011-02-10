#!/usr/bin/env python

from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks
import numpy as np

def main(args) :

    for afile in args.trackfiles :
        tracks, falarms = FilterMHTTracks(*ReadTracks(afile))

        print afile, ':'
        print "Track Cnt: %.4d  False Alarm Cnt: %.4d" % (len(tracks), len(falarms))
        print "Mean Length:", np.mean([len(aTrack) for aTrack in tracks])
        

if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Report on each given trackfile.")
    AddCommandParser('TrackReports', parser)

    args = parser.parse_args()

    main(args)



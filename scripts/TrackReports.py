#!/usr/bin/env python

from ZigZag.TrackFileUtils import ReadTracks
from ZigZag.TrackUtils import FilterMHTTracks
import numpy as np

"""
_lineItems = [{'name': 'Track Cnt',
               'type': 'scalar',
               'func': lambda tracks, falarms : len(tracks)},

              {'name': 'False Alarm Cnt',
               'type': 'scalar',
               'func': lambda tracks, falarms : len(falarms)},

              {'name': 'Length',
               'type': ['',
               'func': lambda tracks, falarms : np.sum(np.hypot(*np.diff((aTrack['xLocs'], aTrack['yLocs']))))

def CalcReport(lineItems, tracks, falarms) :
    


def DispReport(lineItems, reportData) :
    pass
"""

def main(args) :

    for afile in args.trackfiles :
        tracks, falarms = FilterMHTTracks(*ReadTracks(afile))
        dists, lens = zip(*[(np.sum(np.hypot(*np.diff((aTrack['xLocs'], aTrack['yLocs'])))),
                             len(aTrack))
                            for aTrack in tracks])
        

        print
        print afile, ':'
        print "Track Cnt: %4d" % len(tracks)
        print "False Alarm Cnt: %4d" % len(falarms)
        print "Max  Length: %4d Frames, %8.3f km" % (np.max(lens), np.max(dists))
        print "Mean Length: %4d Frames, %8.3f km" % (np.mean(lens), np.mean(dists))
        print "Min  Length: %4d Frames, %8.3f km" % (np.min(lens), np.min(dists))
        
        

if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Report on each given trackfile.")
    AddCommandParser('TrackReports', parser)

    args = parser.parse_args()

    main(args)



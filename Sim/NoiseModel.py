import numpy
import numpy.lib.recfunctions as nprf   # for .append_fields()
from scipy.spatial import KDTree


noise_modelList = {}

def _noise_register(modelclass, name, argValidator) :
    if name in noise_modelList :
        raise ValueError("%s is already a registered noise maker." % name)

    noise_modelList[name] = (modelclass, argValidator)


class NoiseModel(object) :
    pass



class TrackNoise(NoiseModel) :
    """
    Noisify the positions of the points in a track.
    """
    def __init__(self, loc_variance) :
        self._loc_variance = loc_variance

    def __call__(self, tracks, falarms, tLims) :
        for aTrack in tracks :
            aTrack['xLocs'] += self._loc_variance * numpy.random.randn(len(aTrack))
            aTrack['yLocs'] += self._loc_variance * numpy.random.randn(len(aTrack))

_noise_register(TrackNoise, "PosNoise", dict(loc_variance="float(min=0)"))


class FalseMerge(NoiseModel) :
    """
    Perform random "false mergers" of the tracks.
    """

    def __init__(self, false_merge_prob, false_merge_dist) :
        self._false_merge_prob = false_merge_prob
        self._false_merge_dist = false_merge_dist

    def __call__(self, tracks, falarms, tLims) :
        # False mergers in this algorithm is only done
        # between tracks.  False Alarms are not included.
        # This hstack call is merging all the tracks together into one massive array.
        #   Plus, for each track, a trackID is appended on for each point in the track
        #   to help identify the track a point came from.
        trackStrms = numpy.hstack([nprf.append_fields(aTrack, 'trackID',
                                                      [trackIndex] * len(aTrack),
                                                      usemask=False)
                                   for trackIndex, aTrack in enumerate(tracks)])

        # Go frame by frame to see which storms could be occluded.
        for volTime in xrange(min(tLims), max(tLims) + 1) :
            strmCells = trackStrms[trackStrms['frameNums'] == volTime]

            # Don't bother if there are only one or no strmCells for this moment in time
            if len(strmCells) <= 1 :
                continue

            tree = KDTree(zip(strmCells['xLocs'], strmCells['yLocs']))

            candidatePairs = list(tree.query_pairs(self._false_merge_dist))
            pointsRemoved = set([])
            for aPair in candidatePairs :
                if aPair[0] in pointsRemoved or aPair[1] in pointsRemoved :
                    # One of these points have already been removed, skip this pair
                    continue

                strm1Cell = strmCells[aPair[0]]
                strm2Cell = strmCells[aPair[1]]
                strm1TrackID = strm1Cell['trackID']
                strm2TrackID = strm2Cell['trackID']

                if (len(tracks[strm1TrackID]) > 3
                    and len(tracks[strm2TrackID]) > 2
                    and (numpy.random.uniform(0.1, 1.0) *
                         numpy.hypot(strm1Cell['xLocs'] - strm2Cell['xLocs'],
                                     strm1Cell['yLocs'] - strm2Cell['yLocs'])
                         / self._false_merge_dist < self._false_merge_prob)) :
                    # If the tracks are long enough, and the PRNG determines that a false
                    #   merger should occur, then add this point to the list and then
                    #   rebuild the list of points for the track without the removed point.
                    pointsRemoved.add(aPair[0])
                    tracks[strm1TrackID] = tracks[strm1TrackID][strm1Cell['cornerIDs']
                                                  != tracks[strm1TrackID]['cornerIDs']]


_noise_register(FalseMerge, 'FalseMerge', dict(false_merge_prob="float(min=0, max=1)",
                                               false_merge_dist="float(min=0)"))

class DropOut(NoiseModel) :
    def __init__(self, dropout_prob) :
       self._dropout_prob = dropout_prob

    def __call__(self, tracks, falarms, tLims) :
        for trackIndex in range(len(tracks)) :
            trackLen = len(tracks[trackIndex])
            stormsToKeep = numpy.random.random_sample(trackLen) >= self._dropout_prob
            tracks[trackIndex] = tracks[trackIndex][stormsToKeep]

_noise_register(DropOut, 'DropOut', dict(dropout_prob="float(min=0, max=1)"))

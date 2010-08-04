import numpy
import numpy.lib.recfunctions as nprf   # for .append_fields()


noise_modelList = {}

def _noise_register(modelclass, name) :
    if name in noise_modelList :
        raise ValueError("%s is already registered" % name)

    noise_modelList[name] = modelclass


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

_noise_register(TrackNoise, "PosNoise")


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
            # Calc the distances between each storm cell in this volume
            distMatrix = numpy.hypot(strmCells['xLocs'] - numpy.atleast_2d(strmCells['xLocs']).T,
                                     strmCells['yLocs'] - numpy.atleast_2d(strmCells['yLocs']).T)


            # take a storm cell, and see if there is a false merger
            for strm1Index in xrange(len(strmCells)) :
                strm1TrackID = strmCells['trackID'][strm1Index]

                # ...check strm1 against the remaining storm cells.
                # TODO: Maybe use some sort of diag or tri function
                #       or maybe kdtrees?
                # to get all the possible combinations in an orderly manner?
                # However, for now, this works just fine.
                for strm2Index in xrange(strm1Index, len(strmCells)) :
                    strm2TrackID = strmCells['trackID'][strm2Index]

                    # See if the two points are close enough together (false_merge_dist),
                    # and see if it satisfy the random chance of being merged
                    if (distMatrix[strm1Index, strm2Index] <= self._false_merge_dist and
                        len(tracks[strm1TrackID]) > 3 and len(tracks[strm2TrackID]) > 2 and
                        (numpy.random.uniform(0., 1.) * distMatrix[strm1Index, strm2Index] /
                             self._false_merge_dist < self._false_merge_prob)) :

                        #print "\nWe have Occlusion!  trackID1: %d  trackID2:  %d   frameNum: %d\n" % (trackID1, trackID2, aVol['volTime'])
                        #print tracks[trackID1]['frameNums']

                        # Ok, we will have strm1 occluded by strm2, remove it from the track
                        tracks[strm1TrackID] = \
                            tracks[strm1TrackID][numpy.logical_not(tracks[strm1TrackID]['frameNums'] == \
                                                                   volData[volIndex]['volTime'])]

                    # No need to continue searching strm2s against this strm1
                    break

_noise_register(FalseMerge, 'FalseMerge')

class DropOut(NoiseModel) :
    def __init__(self, dropout_prob) :
       self._dropout_prob = dropout_prob

    def __call__(self, tracks, falarms, tLims) :
        pass

_noise_register(DropOut, 'DropOut') 

import ZigZag.TrackUtils as TrackUtils
import numpy

gen_modelList = {}

def _gen_register(modelclass, name, argValidator) :
    if name in gen_modelList :
        raise ValueError("%s is already a registered generator" % name)

    gen_modelList[name] = (modelclass, argValidator)

class TrackGenerator(object) :
    def __init__(self, initModel, motionModel, trackMaker) :
        self._initModel = initModel
        self._motionModel = motionModel
        self._trackMaker = trackMaker


    def __call__(self, cornerID, trackCnt, simState, *makerParams) :
        theTracks = []
        theFAlarms = []
        for index in range(trackCnt) :
            newTrack = self._trackMaker(cornerID, self._initModel,
                                        self._motionModel, *makerParams)

            cornerID += len(newTrack)
            theTracks.append(numpy.sort(newTrack, 0, order=['frameNums']))

        return theTracks, theFAlarms, cornerID

_gen_register(TrackGenerator, 'Tracker', dict(init="string",
                                              motion="string",
                                              trackmaker="string"))

class NullGenerator(TrackGenerator) :
    def __init__(self) :
        TrackGenerator.__init__(self, None, None, None)

    def __call__(self, cornerID, trackCnt, simState, *makerParams) :
        return [], [], cornerID

_gen_register(NullGenerator, 'Processing', dict())


class SplitGenerator(TrackGenerator) :

    def __init__(self, initModel, motionModel, trackMaker):
        TrackGenerator.__init__(self, initModel, motionModel, trackMaker)
        # Tracks are analyzed from 0 to end
        self._trackSort = 1


    def __call__(self, cornerID, trackCnt, simState, *makerParams) :
        theTracks = []
        theFAlarms = []
        # Now, split/merge some of those tracks
        validTracks, = numpy.nonzero(numpy.array(simState['theTrackLens']) >= 3)

        # Generate a list of tracks that will have a split/merge
        # Currently, we are sampling without replacement.
        #   Each track can only split at most once in its life.
        tracksToSplit = [simState['theTracks'][validTracks[anIndex]] for anIndex in
                          numpy.random.rand(len(validTracks)).argsort()[:trackCnt]]

        for choosenTrack in tracksToSplit :
            # Merges has self._trackSort == -1,
            # Splits has self._trackSort == 1.
            # When merging, we want the track reversed so that we do a split in reverse time.
            choosenTrack = choosenTrack[::self._trackSort]

            # Choose a frame to initiate a split.
            # Note, I want a frame like how I want my sliced bread,
            #       no end-pieces!
            frameIndex = numpy.random.random_integers(1, len(choosenTrack) - 2)
            self._initModel.setsplit(choosenTrack, choosenTrack[frameIndex]['frameNums'],
                                                   choosenTrack[frameIndex]['xLocs'],
                                                   choosenTrack[frameIndex]['yLocs'])
            newTrack = self._trackMaker(cornerID, self._initModel, self._motionModel, *makerParams)
            cornerID += len(newTrack)
            theTracks.append(numpy.sort(newTrack, 0, order=['frameNums']))

        return theTracks, theFAlarms, cornerID

_gen_register(SplitGenerator, "Splitter", dict(init="string",
                                               motion="string",
                                               trackmaker="string"))

class MergeGenerator(SplitGenerator) :
    def __init__(self, initModel, motionModel, trackMaker):
        SplitGenerator.__init__(self, initModel, motionModel, trackMaker)
        # Tracks are analyzed from end to 0
        self._trackSort = -1

_gen_register(MergeGenerator, "Merger", dict(init="string",
                                             motion="string",
                                             trackmaker="string"))


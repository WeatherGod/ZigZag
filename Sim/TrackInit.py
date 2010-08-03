import numpy

init_modelList = {}

#############################
#   Initialization Models
#############################
class InitModel(object) :
    def __init__(self) :
        self._initFrame = None
        self._initXPos = None
        self._initYPos = None
        self._initSpeed = None
        self._initHeading = None

    def __call__(self) :
        return (self._initFrame, self._initXPos, self._initYPos,
                                 self._initSpeed * numpy.cos(self._initHeading),
                                 self._initSpeed * numpy.sin(self._initHeading))


class SplitInit(InitModel) :
    useInitState = False

    def __init__(self, speedOff, headOff) :
        """
        speedOff, headOff is the change in the speed and heading that the 
        new storm will have compared to the heading of the parent track, in degrees.
        """
        InitModel.__init__(self)
        self._speedOff = speedOff
        self._headOff = headOff

    def setsplit(self, parentTrack, frameNums, xLocs, yLocs) :
        """
        frameNum, xPos, yPos specifies the initial position of the
        track that splits off.  Note that this position will not be
        reported however because it already exists in the parent track.

        parentTrack is the track data that can be used to analyze and
        help initialize the characteristics of the new storm.
        """
        self._initFrame = frameNums
        self._initXPos = xLocs
        self._initYPos = yLocs
        xDiffs = numpy.diff(parentTrack['xLocs'])
        yDiffs = numpy.diff(parentTrack['yLocs'])
        tDiffs = numpy.diff(parentTrack['frameNums'])
        angles = numpy.arctan2(yDiffs, xDiffs)
        self._initSpeed = numpy.mean(numpy.sqrt(xDiffs**2 + yDiffs**2)/tDiffs) + self._speedOff
        self._initHeading = numpy.arctan2(numpy.sum(numpy.sin(angles)),
                                          numpy.sum(numpy.cos(angles))) + (self._headOff * numpy.pi / 180.0)

    def __call__(self) :
        return InitModel.__call__(self)

init_modelList['SplitInit'] = SplitInit

class NormalInit(InitModel) :
    useInitState = True

    def __init__(self, tLims, xPos, yPos, xScale, yScale, speedLims, headingLims) :
        """
        tLims : tuple of ints
            Start and end frames  E.g., (5, 12)

        xPos, yPos : floats
            Mean location for the center of the initial positions.

        xScale, yScale : floats
            The spread of the initial positions.

        headingLims : tuple of floats
            The limits of the initial angle that a track may move.
            The units is in degrees and is using math coordinates.
            I.E., 0.0 degrees is East, 90.0 degrees is North.
            Ex: (30.0, 60.0) to generally head NorthEast.
            Note that, like xPosLims, this constraint is only applied
            to the initialization, and the track may head anywhere afterwards.

        speedLims : tuple of floats
            The limits of the initial speed (in magnitude) that a track
            may have. Note that this constraint is only
            applied to the initialization and the track may have any
            speed afterwards.
            Ex: (5.0, 25.0)
        """
        InitModel.__init__(self)
        self.tLims = (min(tLims), max(tLims))
        self.xPos = xPos
        self.yPos = yPos
        self.xScale = xScale
        self.yScale = yScale
        self.speedLims = (min(speedLims), max(speedLims))
        self.headingLims = (min(headingLims), max(headingLims))

    def __call__(self) :
        self._initFrame = numpy.random.randint(*self.tLims)
        self._initXPos = self.xScale * numpy.random.randn(1) + self.xPos
        self._initYPos = self.yScale * numpy.random.randn(1) + self.yPos
        self._initSpeed = numpy.random.uniform(*self.speedLims)
        self._initHeading = numpy.random.uniform(*self.headingLims) * (numpy.pi / 180.0)

        return InitModel.__call__(self)

init_modelList['NormalInit'] = NormalInit


class UniformInit(InitModel) :
    useInitState = True

    def __init__(self, tLims, xLims, yLims, speedLims, headingLims) :
        """
        tLims : tuple of ints
            Start and end frames  E.g., (5, 12)

        xLims, yLims : tuple of floats
            The spatial domain for track initialization
            Note that this constraint is *not* applied to
            subsequent states of the track point.  In other
            words, the track can leave/enter the domain at will.
            Ex: (0.0, 255.0)

        headingLims : tuple of floats
            The limits of the initial angle that a track may move.
            The units is in degrees and is using math coordinates.
            I.E., 0.0 degrees is East, 90.0 degrees is North.
            Ex: (30.0, 60.0) to generally head NorthEast.
            Note that, like xPosLims, this constraint is only applied
            to the initialization, and the track may head anywhere afterwards.

        speedLims : tuple of floats
            The limits of the initial speed (in magnitude) that a track
            may have. Note that, like xPosLims, this constraint is only
            applied to the initialization and the track may have any
            speed afterwards.
            Ex: (5.0, 25.0)
        """
        InitModel.__init__(self)
        self.tLims = (min(tLims), max(tLims))
        self.xPosLims = (min(xLims), max(xLims))
        self.yPosLims = (min(yLims), max(yLims))
        self.speedLims = (min(speedLims), max(speedLims))
        self.headingLims = (min(headingLims), max(headingLims))

    def __call__(self) :
        self._initFrame = numpy.random.randint(*self.tLims)
        self._initXPos = numpy.random.uniform(*self.xPosLims)
        self._initYPos = numpy.random.uniform(*self.yPosLims)
        self._initSpeed = numpy.random.uniform(*self.speedLims)
        self._initHeading = numpy.random.uniform(*self.headingLims) * (numpy.pi / 180.0)

        return InitModel.__call__(self)

init_modelList['UniformInit'] = UniformInit

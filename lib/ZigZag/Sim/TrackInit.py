import numpy as np

init_modelList = {}

def _init_register(modelclass, name, argValidator) :
    if name in init_modelList :
        raise ValueError("%s is already a registered track initializer." % name)

    init_modelList[name] = (modelclass, argValidator)

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
                                 self._initSpeed * np.cos(self._initHeading),
                                 self._initSpeed * np.sin(self._initHeading))


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
        xDiffs = np.diff(parentTrack['xLocs'])
        yDiffs = np.diff(parentTrack['yLocs'])
        tDiffs = np.diff(parentTrack['frameNums'])
        angles = np.arctan2(yDiffs, xDiffs)
        self._initSpeed = np.mean(np.sqrt(xDiffs**2 + yDiffs**2)/tDiffs) + self._speedOff
        self._initHeading = np.arctan2(np.sum(np.sin(angles)),
                                       np.sum(np.cos(angles))) + (self._headOff * np.pi / 180.0)

    def __call__(self) :
        return InitModel.__call__(self)

_init_register(SplitInit, 'SplitInit', dict(speedOff="float(min=0.0)",
                                            headOff="float(min=-360.0, max=360.0)"))

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
        self._initFrame = np.random.randint(*self.tLims)
        self._initXPos = self.xScale * np.random.randn(1) + self.xPos
        self._initYPos = self.yScale * np.random.randn(1) + self.yPos
        self._initSpeed = np.random.uniform(*self.speedLims)
        self._initHeading = np.random.uniform(*self.headingLims) * (np.pi / 180.0)

        return InitModel.__call__(self)

_init_register(NormalInit, 'NormalInit', dict(tLims="float_list(min=2, max=2)",
                                              xPos="float", yPos="float",
                                              xScale="float(min=0.0)", yScale="float(min=0.0)",
                                              speedLims="float_list(min=2, max=2)",
                                              headingLims="float_list(min=2, max=2)"))


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
        self._initFrame = np.random.randint(*self.tLims)
        self._initXPos = np.random.uniform(*self.xPosLims)
        self._initYPos = np.random.uniform(*self.yPosLims)
        self._initSpeed = np.random.uniform(*self.speedLims)
        self._initHeading = np.random.uniform(*self.headingLims) * (np.pi / 180.0)


        return InitModel.__call__(self)

_init_register(UniformInit, 'UniformInit', dict(tLims="float_list(min=2, max=2)",
                                                xLims="float_list(min=2, max=2)",
                                                yLims="float_list(min=2, max=2)",
                                                speedLims="float_list(min=2, max=2)",
                                                headingLims="float_list(min=2, max=2)"))

class UniformEllipse(InitModel) :
    useInitState = True

    def __init__(self, tLims, a, b, orient, speedLims, headingLims, xOffset, yOffset, offsetHeading, offsetSpeed) :
        """
        tLims : tuple of ints
            Start and end frames  E.g., (5, 12)

        a, b : floats
            Parameters that correspond to the half-length
            of the major and minor axes, respectively.

        orient : float [0, 360.0]
            The orientation of the ellipse in degrees
            relative to the x-axis.

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

        xOffset, yOffset : floats
            X, Y positions of the center of the ellipse
            at time == min(tLims).

        offsetHeading : float [0, 360.0]
            The direction that the center of the ellipse
            should move with respect to time.
            The angle is in degrees and is with respect
            to the x-axis.

        offsetSpeed : float
            The speed that the center of the ellipse
            should move with respect to time.

        """
        InitModel.__init__(self)
        self.tLims = (min(tLims), max(tLims))
        self.a = a
        self.b = b
        self.orient = orient * (np.pi / 180.0)
        self.rotMatrix = np.array([[np.cos(self.orient), -np.sin(self.orient)],
                                   [np.sin(self.orient), np.cos(self.orient)]])
        self.speedLims = speedLims
        self.headingLims = headingLims
        self.xOffset = xOffset
        self.yOffset = yOffset
        self.offsetHeading = offsetHeading * (np.pi / 180.0)
        self.offsetSpeed = offsetSpeed

    def __call__(self) :
        self._initFrame = np.random.randint(*self.tLims)
        self._initSpeed = np.random.uniform(*self.speedLims)
        self._initHeading = np.random.uniform(*self.headingLims) * (np.pi / 180.0)
        r = np.random.uniform(0.0, 1.0)
        phi = np.random.uniform(0.0, 1.0) * 2.0 * np.pi
        # Create a random point within a uniform circle.
        # Note the sqrt(r), which ensures that the distribution
        # of points is uniform. Just using r would cause
        # a bias towards the origin
        coords = np.sqrt(r) * np.array([np.cos(phi),
                                        np.sin(phi)])

        # Scale the unit circle to be like an ellipse
        coords *= np.array([self.a, self.b])

        # Rotate the ellipse
        coords = np.dot(self.rotMatrix, coords)

        # Translate the ellipse a distance depending on the time
        coords += (np.array([self.xOffset, self.yOffset])
                   + (self.offsetSpeed * (self._initFrame - self.tLims[0])
                      * np.array([np.cos(self.offsetHeading),
                                  np.sin(self.offsetHeading)])))

        self._initXPos, self._initYPos = coords

        return InitModel.__call__(self)

_init_register(UniformEllipse, 'EllipseUni', dict(tLims="float_list(min=2, max=2)",
                                              a="float", b="float",
                                              orient="float(min=-360.0, max=360.0)",
                                              xOffset="float", yOffset="float",
                                              speedLims="float_list(min=2, max=2)",
                                              headingLims="float_list(min=2, max=2)",
                                              offsetSpeed="float(min=0.0)",
                                              offsetHeading="float(min=-360.0, max=360.0)"))


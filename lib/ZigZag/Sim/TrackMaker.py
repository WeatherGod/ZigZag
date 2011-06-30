from numpy import random

#############################
#   Track Making
#############################
class TrackPoint(object) :
    """
    TrackPoint is a useful data object that helps with making simulated tracks.
    When created, it will randomly initialize itself, according to parameters, to
    give it a random starting time, position, speed and direction.

    Then, the object can be simply iterated in a for loop to update its state.
    When it 'dies', or it reached the predetermined end-of-life, the iterator
    will stop (just like looping through an array or a file).

    Each iteration will yield a tuple of (trackStatus, xPos, yPos, frameNum).
    Note that track status is currently always 'M' to indicate a good track.
    Future revisions may make this a little bit more robust and allow for
    tracks to disappear and such, thereby changing its status, maybe?

    """

    def __init__(self, cornerID, trackDeathProb, deltaT,
                       initModel, motionModel, maxLen = 50) :
        """
        Create a point that will be used to create a track.

        Parameters
        ----------
        cornerID : int
            Integer to use to begin incrementally ID-ing the points generated.

        trackDeathProb : float between 0 and 1
            The probability that a track will die at some particular iteration.
            0.0 for eternal tracks, 1.0 for single points.

        deltaT : float
            The time step for each frame in the track.

        maxLen : int
            Maximum length of the track
        """
        # These are "read-only" properties that are used in iterating
        self.trackDeathProb = trackDeathProb
        self.cornerID = cornerID
        self._motionModel = motionModel
        self._framesRemain = maxLen
        self.deltaT = deltaT

        # Just a stub for now...
        self.strm_size = 0.

        # These are the internal state variables that will change
        # subsequent calls will update the state.
        self.frameNum, self.xLoc, self.yLoc, self.xSpeed, self.ySpeed = initModel()
        #print self.frameNum, self.xLoc, self.yLoc, self.xSpeed, self.ySpeed

        # Determine if this initial state is to be reported
        self._useInitState = initModel.useInitState
        # Used to prevent the track-maker from killing a track in the first call to next()
        self._isFirstCall = True

    def __iter__(self) :
        return self

    def next(self) :
        """
        Each iteration through the loop will cause the point to "move" itself according to
        a psuedo-constant velocity model.
        """
        if self._useInitState :
            # Then this is the first call to next() and the initial data is to be used
            self._useInitState = False
        else :
            if (not self._isFirstCall and
                (random.uniform(0.0, 1.0) <= self.trackDeathProb
                 or self._framesRemain <= 0)) :
                raise StopIteration

            dFrame, dx, dy, dVelx, dVely = self._motionModel(self.deltaT, self.xSpeed, self.ySpeed)
#            print type(self.frameNum), type(dFrame), dx, dy, dVelx, dVely
            self.frameNum += dFrame
            self.xLoc += dx
            self.yLoc += dy
            self.xSpeed += dVelx
            self.ySpeed += dVely
            self.cornerID += 1 if not self._isFirstCall else 0

        self._framesRemain -= 1
        self._isFirstCall = False
        return self.xLoc, self.yLoc, self.strm_size, self.cornerID, self.frameNum, 'M'

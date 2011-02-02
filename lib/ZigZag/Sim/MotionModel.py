import numpy

motion_modelList = {}

def _motion_register(modelclass, name, argValidator) :
    if name in motion_modelList :
        raise ValueError("%s is already a registered motion model." % name)

    motion_modelList[name] = (modelclass, argValidator)

#############################             
#   Motion Models
#############################
class MotionModel(object) :
    def __init__(self) :
        pass

    def __call__(self) :
        return None
    
class ConstVel_Model(MotionModel) :
    def __init__(self, deltaFrame, velModify) :
        """
        Create a new piece-wise constant velocity motion model.

        This model changes randomly changes the speed of the track
             according to a uniform distribution with a range of +/- velModify.

        deltaFrame : int
            The frame increment

        velModify : float
            The variance (+/-) of the uniform noise to apply to the x/y speed
            of the track point for each iteration of the track.
        """
        MotionModel.__init__(self)
#        print type(deltaFrame), type(velModify)
        self.deltaFrame = deltaFrame
        self.velModify = velModify

    def __call__(self, deltaT, xSpeed, ySpeed) :
        dx = self.deltaFrame * deltaT * xSpeed
        dy = self.deltaFrame * deltaT * ySpeed
        dVelx = numpy.random.uniform(-self.velModify, self.velModify)
        dVely = numpy.random.uniform(-self.velModify, self.velModify)
        return self.deltaFrame, dx, dy, dVelx, dVely

_motion_register(ConstVel_Model, 'ConstVel_Model', dict(deltaFrame="integer",
                                                        velModify="float(min=0)"))


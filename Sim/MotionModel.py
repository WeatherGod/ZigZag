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
    def __init__(self, deltaT, velModify) :
        """
        Create a new piece-wise constant velocity motion model.

        This model changes randomly changes the speed of the track
             according to a uniform distribution with a range of +/- velModify.

        deltaT : float or int
            The time increment

        velModify : float
            The variance (+/-) of the uniform noise to apply to the x/y speed
            of the track point for each iteration of the track.
        """
        MotionModel.__init__(self)
        self.deltaT = deltaT
        self.velModify = velModify

    def __call__(self, xSpeed, ySpeed) :
        dx = self.deltaT * xSpeed
        dy = self.deltaT * ySpeed
        dVelx = numpy.random.uniform(-self.velModify, self.velModify)
        dVely = numpy.random.uniform(-self.velModify, self.velModify)
        return self.deltaT, dx, dy, dVelx, dVely

_motion_register(ConstVel_Model, 'ConstVel_Model', dict(deltaT="float",
                                                        velModify="float(min=0)"))

from __future__ import print_function
import numpy as np

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
        ..note:
            Well, this isn't exactly a constant velocity model. You
            probably really want ConstVel2_Model.  This is kept for
            backwards compatibility.

        This model changes randomly changes the speed of the track
             according to a uniform distribution with a range of +/- velModify.

        deltaFrame : int
            The frame increment

        velModify : float
            The variance (+/-) of the uniform noise to apply to the x/y speed
            of the track point for each iteration of the track.
            This should be in the same units as an acceleration term.
            The name *velModify* is kept for backwards compatibility.
        """
        MotionModel.__init__(self)
#        print(type(deltaFrame), type(velModify))
        self.deltaFrame = deltaFrame
        self.accelTerm = velModify

    def __call__(self, deltaT, xSpeed, ySpeed) :
        dx = self.deltaFrame * deltaT * xSpeed
        dy = self.deltaFrame * deltaT * ySpeed
        velModify = self.accelTerm * deltaT
        dVelx = np.random.uniform(-velModify, velModify)
        dVely = np.random.uniform(-velModify, velModify)
        return self.deltaFrame, dx, dy, dVelx, dVely

_motion_register(ConstVel_Model, 'ConstVel_Model', dict(deltaFrame="integer",
                                                        velModify="float(min=0)"))

class ConstVel2_Model(MotionModel) :
    def __init__(self, deltaFrame, angleModify, spdModify) :
        """
        Create a new constant velocity motion model.

        This model applies random perturbations to the instantaneous speed and
             direction of the track according to a uniform distribution
             with a range of +/- angleModify and +/- spdModify.

        deltaFrame : int
            The frame increment

        angleModify : float
            The variance (+/-) of the uniform noise to apply to the direction
            of the track at each iteration of the track.
            This should be in units of degrees per unit time.

        spdModify : float
            The variance (+/-) of the uniform noise to apply to the magnitude
            speed of the track at each iteration of the track.
            This should be in units of distance per (unit time)**2
        """
        MotionModel.__init__(self)
        self.deltaFrame = deltaFrame
        self.accelTerm = spdModify
        self.angleTerm = np.radians(angleModify)

    def __call__(self, deltaT, xSpeed, ySpeed) :
        dx = self.deltaFrame * deltaT * xSpeed
        dy = self.deltaFrame * deltaT * ySpeed

        angleModify = self.angleTerm * deltaT
        dAngle = np.random.uniform(-angleModify, angleModify)
        spdModify = self.accelTerm * deltaT
        dSpd = np.random.uniform(-spdModify, spdModify)

        dVelx = dSpd * np.cos(dAngle)
        dVely = dSpd * np.sin(dAngle)

        dx += dVelx * deltaT * self.deltaFrame
        dy += dVely * deltaT * self.deltaFrame

        return self.deltaFrame, dx, dy, 0.0, 0.0

_motion_register(ConstVel2_Model, 'ConstVel2_Model',
                 dict(deltaFrame="integer",
                      angleModify="float(min=0, max=360)",
                      spdModify="float(min=0)"))

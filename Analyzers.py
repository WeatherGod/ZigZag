import numpy
import scipy

skillcalcs = {}
def _register_trackskill(func, name) : 
    if name in skillcalcs :
        raise ValueError("%s is already a registered track skill measure." % name)

    skillcalcs[name] = func

def CalcHeidkeSkillScore(truthTable, **kwargs) :
    """
    Skill score formula from 
    http://www.eumetcal.org.uk/eumetcal/verification/www/english/msg/ver_categ_forec/uos3/uos3_ko1.htm

    HSS = 2(ad - bc) / [(a + c)(c + d) + (a + b)(b + d)]

    Note that a forecast is good when it is closer to 1, and
    is worse if less than zero.

                Observed
              True    False
Forecasted
    True       a        b
    False      c        d
    """

    a = float(len(truthTable['assocs_Correct']))
    b = float(len(truthTable['assocs_Wrong']))
    c = float(len(truthTable['falarms_Wrong']))
    d = float(len(truthTable['falarms_Correct']))
    denom = ((a + c) * (c + d)) + ((a + b) * (b + d))
    if denom < 0.1 :
       # Prevent division by zero...
       return 1.0
    else :
       return 2. * ((a * d) - (b * c)) / denom

_register_trackskill(CalcHeidkeSkillScore, "HSS")


def CalcTrueSkillStatistic(truthTable, **kwargs) :
    """
    Skill score formula from 
    http://euromet.meteo.fr/resources/ukmeteocal/verification/www/english/msg/ver_categ_forec/uos3/uos3_ko2.htm

    TSS = (ad - bc) / [(a + c)(b + d)]

    Note that a forecast is good when it is closer to 1, and
    is worse if closer to -1.

                Observed
              True    False
Forecasted
    True       a        b
    False      c        d
    """

    a = float(len(truthTable['assocs_Correct']))
    b = float(len(truthTable['assocs_Wrong']))
    c = float(len(truthTable['falarms_Wrong']))
    d = float(len(truthTable['falarms_Correct']))
    denom = (a + c) * (b + d)
    if denom < 0.1 :
        # Prevent division by zero...
        return 1.0
    else :
        return ((a * d) - (b * c)) / denom

_register_trackskill(CalcTrueSkillStatistic, "TSS")

def Skill_TrackLen(tracks, **kwargs) :
    """
    Using one of Lak's measures for goodness of tracking  -- median length/duration of tracks
    """
    return numpy.median([aTrack['frameNums'].ptp() for aTrack in tracks])

_register_trackskill(Skill_TrackLen, "Dur")

def Skill_LineErr(tracks, **kwargs) :
    """
    Using one of Lak's measures for goodness of tracking -- mean RMSE of
    the tracks against their respective best-fit lines.
    """
    fiterr = []
    for aTrack in tracks :
        if len(aTrack) < 3 :
            continue
        a, b = scipy.polyfit(aTrack['xLocs'], aTrack['yLocs'], 1)
        y_fit = scipy.polyval([a, b], aTrack['xLocs'])
        fiterr.append(numpy.sqrt(numpy.mean((aTrack['yLocs'] - y_fit)**2)))
    return numpy.mean(fiterr)

_register_trackskill(Skill_LineErr, "Line")


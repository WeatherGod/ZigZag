import numpy as np
import scipy

skillcalcs = {}
def _register_trackskill(func, name) : 
    if name in skillcalcs :
        raise ValueError("%s is already a registered track skill measure." % name)

    skillcalcs[name] = func

_contingency_diagram = \
"""
                Observed
              True    False
Forecasted
    True       a        b
    False      c        d
"""

def _breakup_truthtable(truthTable) :
    a = len(truthTable['assocs_Correct'])
    b = len(truthTable['assocs_Wrong'])
    c = len(truthTable['falarms_Wrong'])
    d = len(truthTable['falarms_Correct'])

    return a, b, c, d

def CalcPercentCorrect(truthTable, **kwargs) :
    """
    Percent Correct from "Statistical Methods in the Atmospheric Sciences"
    by Daniel S. Wilks (2nd Edition) on page 262.

    PC = (a + d) / n

    A forecast is better when closer to 1, and at its worst when zero.

    This skill score is probably better suited for scoring tracking algorithms.
    This is because the majority of the data will be the track associations,
    while there may be little (or even none) of non-associations.
    In HSS and TSS, if d was zero or very small due to lack of noisy data,
    then it didn't matter how well the tracker was in making associations,
    the resulting score will be unfairly set to very small (or even negative!).
    """

    a, b, c, d = _breakup_truthtable(truthTable)

    n = float(a + b + c + d)
    return (a + d) / n

_register_trackskill(CalcPercentCorrect, 'PC')
CalcPercentCorrect.__doc__ += _contingency_diagram



def GilbertSkillScore(truthTable, **kwargs) :
    """
    Skill Score formula from "Statistical Methods in the Atmospheric Sciences"
    by Daniel S. Wilks (2nd Edition) on page 267.

    GSS = (a - a_ref) / (a - a_ref + b + c)

    where a_ref = (a + b)(a + c)/n          .

    Note that a forecast is better when closer to 1, and
    worse if less than zero.

                Observed
              True    False
Forecasted
    True       a        b
    False      c        d
    """
    a, b, c, d = _breakup_truthtable(truthTable)

    n = float(a + b + c + d)
    a_ref = float((a + b) * (a + c)) / n

    return (a - a_ref) / (a - a_ref + b + c)

_register_trackskill(GilbertSkillScore, "GSS")

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
    a, b, c, d = _breakup_truthtable(truthTable)
    denom = ((a + c) * (c + d)) + ((a + b) * (b + d))
    if denom == 0 :
       # Prevent division by zero...
       return 1.0
    else :
       return 2. * ((a * d) - (b * c)) / float(denom)

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

    a, b, c, d = _breakup_truthtable(truthTable)
    denom = (a + c) * (b + d)
    if denom == 0 :
        # Prevent division by zero...
        return 1.0
    else :
        return ((a * d) - (b * c)) / float(denom)

_register_trackskill(CalcTrueSkillStatistic, "TSS")

def Skill_TrackLen(tracks, **kwargs) :
    """
    Using one of Lak's measures for goodness of tracking  -- median length/duration of tracks
    """
    return np.median([aTrack['frameNums'].ptp() for aTrack in tracks])

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
        fiterr.append(np.sqrt(np.mean((aTrack['yLocs'] - y_fit)**2)))
    return np.mean(fiterr)



_register_trackskill(Skill_LineErr, "Line")



def TrackCoherency(true_tracks, tracks, truthTable, **kwargs) :
    """
    Determine the average percent correct of a track
    """
    pass

_register_trackskill(TrackCoherency, "Coherent")



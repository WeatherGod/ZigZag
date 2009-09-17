#!/usr/bin/env python

from TrackSim import TrackSim
from ParamUtils import *			# for SaveSimulationParams, SetupSimParser,
					# ParamsFromOptions
from DoTracking import DoTracking
from TrackFileUtils import *
from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), 
					#     CompareSegments(), CalcHeidkeSkillScore()
from optparse import OptionParser
import os				# for os.sep
import random



def DisplaySkillScores(skillScores, skillScoreName) :

    print skillScoreName
    # TODO: Currently assumes only MHT and SCIT trackers...
    # NOTE: Also assumes that the larger skill value is "better".
    winCnt = 0
    print "        MHT        SCIT"
    for (index, (val1, val2)) in enumerate(zip(skillScores['MHT'], skillScores['SCIT'])) :
        print "%3d.  %7.4f    %7.4f   %s" % (index, val1, val2, str(val1 > val2))
        if val1 > val2 : winCnt += 1

    print "-------------------------------"
    print "      %7.4f    %7.4f   %5.3f" % (sum(skillScores['MHT'])/len(skillScores['MHT']),
					    sum(skillScores['SCIT'])/len(skillScores['SCIT']),
					    float(winCnt) / len(skillScores['MHT']))





parser = OptionParser()
parser.add_option("-s", "--sim", dest="simName", type = "string",
                  help="Generate Tracks for SIMNAME",
                  metavar="SIMNAME", default="NewSim")
parser.add_option("-n", "--num", dest="simCnt", type = "int",
		  help="Repeat Simulation N times.",
		  metavar="N", default=1)
SetupParser(parser)

(options, args) = parser.parse_args()

if options.simCnt <= 0 :
    parser.error("ERROR: Invalid N value: %d" % (options.simCnt))


hss = {'SCIT': [], 'MHT': []}
tss = {'SCIT': [], 'MHT': []}

for index in range(0, options.simCnt) :
    simName = options.simName + ("%s%.3d" % (os.sep, index))
    simParams = ParamsFromOptions(options, simName = simName)

    if (not os.path.exists(simName)) :
        os.makedirs(simName)

    SaveSimulationParams(os.sep.join([simName, 'simParams.conf']), simParams)
    (theTracks, theFAlarms) = TrackSim(simParams, simName)
    DoTracking(simParams, simName)

    true_segs = CreateSegments(theTracks, theFAlarms)

    for aTracker in simParams['trackers'] :
        (finalTracks, finalFAlarms) = ReadTracks(simParams['result_filestem'] + '_' + aTracker)
        (finalTracks, finalFAlarms) = FilterMHTTracks(finalTracks, finalFAlarms)
        
        trackerSegs = CreateSegments(finalTracks, finalFAlarms)

        truthTable = CompareSegments(true_segs, theFAlarms, trackerSegs, finalFAlarms)


        hss[aTracker].append(CalcHeidkeSkillScore(truthTable))
        tss[aTracker].append(CalcTrueSkillStatistic(truthTable))



DisplaySkillScores(hss, "HSS")
print "\n\n"
DisplaySkillScores(tss, "TSS")



import random
import os
from optparse import OptionGroup

def SaveSimulationParams(simParamName, simParams) :
    simParamFile = open(simParamName, 'w')
    simParamFile.write("seed = %d\n" % (simParams['theSeed']))
    simParamFile.write("frameCnt = %d\n" % (simParams['frameCnt']))
    simParamFile.write("totalTracks = %d\n" % (simParams['totalTracks']))
    simParamFile.write("speed_variance = %.2f\n" % (simParams['speed_variance']))
    simParamFile.write("mean_dir = %.1f\n" % (simParams['mean_dir']))
    simParamFile.write("angle_variance = %.1f\n" % (simParams['angle_variance']))
    simParamFile.write("endTrackProb = %.5f\n" % (simParams['endTrackProb']))
    simParamFile.write("xLims = %f %f\n" % (min(simParams['xLims']), max(simParams['xLims'])))
    simParamFile.write("yLims = %f %f\n" % (min(simParams['yLims']), max(simParams['yLims'])))
    simParamFile.write("speedLims = %f %f\n" % (min(simParams['speedLims']), max(simParams['speedLims'])))

    simParamFile.write("false_merge_dist = %.2f\n" % (simParams['false_merge_dist']))
    simParamFile.write("false_merge_prob = %.5f\n" % (simParams['false_merge_prob']))

    simParamFile.write("simTrackFile = " + simParams['simTrackFile'] + "\n")
    simParamFile.write("noisyTrackFile = " + simParams['noisyTrackFile'] + "\n")

    simParamFile.close()

def ReadSimulationParams(simParamName) :
    simParams = {}
    for aLine in open(simParamName, 'r') :
	lineSplit = aLine.split('=')
	keyVal = lineSplit[0].strip()
	assignVal = ''.join(lineSplit[1:]).strip()

	if (keyVal == 'seed' or keyVal == 'frameCnt' or keyVal == 'totalTracks') :
	    assignVal = int(assignVal)
	elif (keyVal == 'speed_variance' or keyVal == 'mean_dir' or 
	      keyVal == 'angle_variance' or keyVal == 'endTrackProb' or
	      keyVal == 'false_merge_dist' or keyVal == 'false_merge_prob') :
	    assignVal = float(assignVal)
	elif (keyVal == 'xLims' or keyVal == 'yLims' or keyVal == 'speedLims') :
	    assignVal = map(float, assignVal.strip().split())

	simParams[keyVal] = assignVal
    
    return simParams

def SetupParser(parser) :
    group = OptionGroup(parser, "Simulation Options",
			"Options for controlling the track simulation.")
    
    group.add_option("--frames", dest="frameCnt", type="int",
		     help="Operate for N frames. (default: %default)",
		     metavar="N", default=12)
    group.add_option("--tracks", dest="totalTracks", type="int",
		     help="Simulate N tracks. (default: %default)",
		     metavar="N", default=30)
    group.add_option("--seed", dest="theSeed", type="int",
		     help="Initialize RNG with SEED. (default: random)",
		     metavar="SEED", default=random.randint(0, 99999999))
    group.add_option("--cleanfile", dest="simTrackFile", type="string",
		     help="Output clean set of tracks to FILE. (default: %default)", 
		     metavar="FILE",
		     default=os.sep.join(["%s", "true_tracks"]))
    group.add_option("--noisyfile", dest="noisyTrackFile", type="string",
		     help="Output noisy set of tracks to FILE. (default: %default)",
		     metavar="FILE",
		     default=os.sep.join(["%s", "noise_tracks"]))
    group.add_option("--trackend", dest="endTrackProb", type="float",
		     help="Probability a track will end for a given frame. (default: %default)",
		     metavar="ENDPROB", default=0.1)
    group.add_option("--direction", dest="mean_dir", type="float",
		     help="Mean direction of tracks in degrees. (default: %default)", 
		     metavar="ANGLE", default=50.0)
    group.add_option("--spd_var", dest="speed_variance", type="float",
		     help="Variance of track speed changes. (default: %default)",
		     metavar="VAR", default=1.5)
    group.add_option("--dir_var", dest="angle_variance", type="float",
		     help="Variance of initial track direction, in degrees. (default: %default)",
		     metavar="VAR", default=20.0)
    group.add_option("--fmerge_dist", dest="false_merge_dist", type="float",
		     help="Distance threshold for false mergers. (default: %default)",
		      metavar="DIST", default=15.)
    group.add_option("--fmerge_prob", dest="false_merge_prob", type="float",
		     help="Probability of false merger for tracks within the DIST threshold. (default: %default)",
		     metavar="PROB", default=0.)

    group.add_option("--xlims", dest="xLims", type="float",
		     nargs = 2,
		     help="Domain limits in x-axis. (default: %default)", 
		     metavar="X1 X2", default=[0., 255.])
    group.add_option("--ylims", dest="yLims", type="float",
		     nargs = 2,
		     help="Domain limits in y-axis. (default: %default)", 
		     metavar="Y1 Y2", default=[0., 255.])
    group.add_option("--spd_lims", dest="speedLims", type="float",
		     nargs = 2,
		     help="Range of speeds for track initialization. (default: %default)", 
		     metavar="SPD1 SPD2", default=[5., 25.])

    parser.add_option_group(group)

    group2 = OptionGroup(parser, "Tracker Options",
                        "Options for controlling the trackers.")
    group2.add_option("--corner", dest="corner_filestem", type="string",
		      help="Corner filename stem. (default = %default)",
		      metavar="CORNER", default=os.sep.join(["%s", "corners"]))
    group2.add_option("--input", dest="inputDataFile", type="string",
		      help="MHT's Input datafile. (default = %default)",
		      metavar="FILE", default=os.sep.join(["%s", "InputDataFile"]))
    group2.add_option("--result", dest="result_filestem", type="string",
		      help="Tracker filename stem for results. (default = %default)",
		      metavar="FILE", default=os.sep.join(["%s", "testResults"]))

    parser.add_option_group(group2)



def ParamsFromOptions(options, simName = None) :
    if simName is None : simName = options.simName

    if options.frameCnt <= 0 :
        parser.error("ERROR: Invalid FrameCnt value: %d" % (options.frameCnt))

    if options.totalTracks <= 0 :
        parser.error("ERROR: Invalid TrackCnt value: %d" % (options.totalTracks))


    if options.false_merge_dist <= 0. :
        parser.error("ERROR: False Merge Dist must be positive! Value: %d" % (options.false_merge_dist))

    if options.false_merge_prob < 0. :
        parser.error("ERROR: False Merge Prob must be positive! Value: %d" % (options.false_merge_prob))

    if options.endTrackProb < 0. :
        parser.error("ERROR: End Track Prob must be positive! Value: %d" % (options.endTrackProb))

    return dict(corner_filestem = options.corner_filestem % simName,
		inputDataFile = options.inputDataFile % simName,
		result_filestem = options.result_filestem % simName,

		simTrackFile = options.simTrackFile % simName,
                noisyTrackFile = options.noisyTrackFile % simName,
                frameCnt = options.frameCnt,
                totalTracks = options.totalTracks,
                speed_variance = options.speed_variance,
                mean_dir = options.mean_dir,
                angle_variance = options.angle_variance,
                endTrackProb = options.endTrackProb,
                xLims = options.xLims,
                yLims = options.yLims,
		tLims = [1, options.frameCnt],
                speedLims = options.speedLims,
                false_merge_dist = options.false_merge_dist,
                false_merge_prob = options.false_merge_prob,
                theSeed = options.theSeed
               )





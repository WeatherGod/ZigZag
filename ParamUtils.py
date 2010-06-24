import random
import os
import argparse

simDefaults = dict( frameCnt = 12,
	            totalTracks = 30,
		    theSeed = 42,
		    simTrackFile = "%s" + os.sep + "true_tracks",
		    noisyTrackFile = "%s" + os.sep + "noise_tracks",
		    endTrackProb = 0.1,
		    mean_dir = 50,
		    speed_variance = 0.75,
		    angle_variance = 20.0,
		    false_merge_dist = 15.0,
		    false_merge_prob = 0.0,
		    xLims = [0.0, 255.0],
		    yLims = [0.0, 255.0],
		    speedLims = [1.0, 6.5])

trackerDefaults = dict(trackers = ['SCIT'],
		       corner_file = "%s" + os.sep + "corners",
		       inputDataFile = "%s" + os.sep + "InputDataFile",
		       result_file = "%s" + os.sep + "testResults")


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
    simParamFile.write("trackers = " + ' '.join(simParams['trackers']) + "\n")

    simParamFile.write("result_file = " + simParams['result_file'] + "\n")
    simParamFile.write("inputDataFile = " + simParams['inputDataFile'] + "\n")
    simParamFile.write("corner_file = " + simParams['corner_file'] + "\n")
    

    simParamFile.close()

def ReadSimulationParams(simParamName) :

    simParams = {}

    # TODO: Should I be copying these?  Am I going to run into an issue with references/objects?
    simParams.update(simDefaults)
    simParams.update(trackerDefaults)

    for aLine in open(simParamName, 'r') :
        # Split string by the equal sign.
	lineSplit = aLine.split('=')

        # The first field will be the key name (stripped of whitespace)
	keyName = lineSplit[0].strip()

        # Backwards compatibility...
	if keyName == "corner_filestem" :
	    keyName = "corner_file"

        # Backwards compatibility...
	if keyName == "result_filestem" :
	    keyName = "result_file"

        # The rest of the fields (in case there is an equal sign somewhere else)
	#     are reconstructed back together, with whitespace stripped AFTER
        #     the reconstruction.  This produces a key/value pair.
	assignVal = '='.join(lineSplit[1:]).strip()

	if keyName in ['seed', 'frameCnt', 'totalTracks'] :
	    # Grab single integer
	    assignVal = int(assignVal)
	elif keyName in ['speed_variance', 'mean_dir', 'angle_variance',
                        'endTrackProb', 'false_merge_dist', 'false_merge_prob']:
            # Grab single float
	    assignVal = float(assignVal)
	elif keyName in ['xLims', 'yLims', 'speedLims'] :
            # Grab array of floats, from a spliting by whitespace
	    assignVal = map(float, assignVal.split())
	elif keyName == 'trackers' :
	    # Grab array of strings, from a spliting by whitespace
	    assignVal = assignVal.split()
	    

	simParams[keyName] = assignVal
    
    simParams['tLims'] = [1, simParams['frameCnt']]
    return simParams

def SetupParser(parser) :
    
    #parser.add_argument_group(SimGroup(parser))
    #parser.add_argument_group(TrackerGroup(parser))
    SimGroup(parser)
    TrackerGroup(parser)



def SimGroup(parser) :
    group = parser.add_argument_group("Simulation Options",
			"Options for controlling the track simulation.")

    
    group.add_argument("--frames", dest="frameCnt", type=int,
		     help="Operate for N frames. (default: %(default)s)",
		     metavar="N", default = simDefaults['frameCnt'])

    group.add_argument("--track_cnt", dest="totalTracks", type=int,
		     help="Simulate N tracks. (default: %(default)s)",
		     metavar="N", default = simDefaults['totalTracks'])

    group.add_argument("--seed", dest="theSeed", type=int,
		     help="Initialize RNG with SEED. (default: %(default)s)",
		     metavar="SEED", default = simDefaults['theSeed'])

    group.add_argument("--cleanfile", dest="simTrackFile", type=str,
		     help="Output clean set of tracks to FILE. (default: %(default)s)", 
		     metavar="FILE",
		     default=simDefaults['simTrackFile'])

    group.add_argument("--noisyfile", dest="noisyTrackFile", type=str,
		     help="Output noisy set of tracks to FILE. (default: %(default)s)",
		     metavar="FILE",
		     default=simDefaults['noisyTrackFile'])

    group.add_argument("--trackend", dest="endTrackProb", type=float,
		     help="Probability a track will end for a given frame. (default: %(default)s)",
		     metavar="ENDPROB", default=simDefaults['endTrackProb'])

    group.add_argument("--direction", dest="mean_dir", type=float,
		     help="Mean direction of tracks in degrees. (default: %(default)s)", 
		     metavar="ANGLE", default=simDefaults['mean_dir'])

    group.add_argument("--spd_var", dest="speed_variance", type=float,
		     help="Variance of track speed changes. (default: %(default)s)",
		     metavar="VAR", default=simDefaults['speed_variance'])

    group.add_argument("--dir_var", dest="angle_variance", type=float,
		     help="Variance of initial track direction, in degrees. (default: %(default)s)",
		     metavar="VAR", default=simDefaults['angle_variance'])

    group.add_argument("--fmerge_dist", dest="false_merge_dist", type=float,
		     help="Distance threshold for false mergers. (default: %(default)s)",
		      metavar="DIST", default=simDefaults['false_merge_dist'])

    group.add_argument("--fmerge_prob", dest="false_merge_prob", type=float,
		     help="Probability of false merger for tracks within the DIST threshold. (default: %(default)s)",
		     metavar="PROB", default=simDefaults['false_merge_prob'])

    group.add_argument("--xlims", dest="xLims", type=float,
		     nargs = 2,
		     help="Domain limits in x-axis. (default: %(default)s)", 
		     metavar="X", default=simDefaults['xLims'])

    group.add_argument("--ylims", dest="yLims", type=float,
		     nargs = 2,
		     help="Domain limits in y-axis. (default: %(default)s)", 
		     metavar="Y", default=simDefaults['yLims'])

    group.add_argument("--spd_lims", dest="speedLims", type=float,
		     nargs = 2,
		     help="Range of speeds for track initialization. (default: %(default)s)", 
		     metavar="SPD", default=simDefaults['speedLims'])

    return group



def TrackerGroup(parser) :
    # TODO: Likely will end up in a separate module, or portion
    group = parser.add_argument_group("Tracker Options",
                        "Options for controlling the trackers.")

    group.add_argument("-t", "--tracker", dest="trackers", type=str,
		     action="append",
                     help="Tracking algorithms to use, in addition to SCIT.  (Ex: MHT)",
                     metavar="TRACKER", default = trackerDefaults['trackers'])

    group.add_argument("--corner", dest="corner_file", type=str,
		     help="Corner filename stem. (default = %(default)s)",
		     metavar="CORNER", default = trackerDefaults['corner_file'])

    group.add_argument("--input", dest="inputDataFile", type=str,
		     help="MHT's Input datafile. (default = %(default)s)",
		     metavar="FILE", default = trackerDefaults['inputDataFile'])

    group.add_argument("--result", dest="result_file", type=str,
		     help="Tracker filename stem for results. (default = %(default)s)",
		     metavar="FILE", default=trackerDefaults['result_file'])

    return group



def ParamsFromOptions(options, simName = None) :
    # NOTE: I do NOT modify the contents of the
    #       options object! This is important for
    #       reusability within a multi-simulation program.
    #       Treat options like a const.
    if simName is None : simName = options.simName

    # Error checking
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

    # NOTE: The default value for these two strings contain
    #       a '%s' in the string.  This will allow for the
    #       simulation name to be used as a part of the filenames.
    #       The user, of course, can choose not to use it.

    # TODO: I can't seem to figure out a generic way to make this work without an 'if/else' statement...
    #       Plus, this doesn't seem very kosher to me...
    if (options.simTrackFile.find('%s') >= 0) : 
        simTrackFile = options.simTrackFile % simName * options.simTrackFile.count('%s')
    else :
        simTrackFile = options.simTrackFile

    if (options.noisyTrackFile.find('%s') >= 0) :
        noisyTrackFile = options.noisyTrackFile % simName * options.noisyTrackFile.count('%s')
    else :
        noisyTrackFile = options.noisyTrackFile

    # TODO: Some of these key/values are temporary.
    #       I will be transistioning to having each tracker
    #	    with its own parameterization file and controls.
    return dict(corner_file = options.corner_file % simName,
		inputDataFile = options.inputDataFile % simName,
		result_file = options.result_file % simName,
	        simTrackFile = simTrackFile,
		noisyTrackFile = noisyTrackFile,
		trackers = options.trackers,
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


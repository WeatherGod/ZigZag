import os       # for os.path.isfile(), os.access(), os.R_OK
import argparse
from configobj import ConfigObj, flatten_errors
from Sim import gen_modelList, noise_modelList, motion_modelList, init_modelList
from validate import Validator
from Trackers import param_confList

simDefaults = dict( frameCnt = 12,
	                totalTracks = 30,
		            seed = 42,
        		    simTrackFile = "true_tracks",
		            noisyTrackFile = "noise_tracks",
                    simConfFile = "simulation.ini",
		            endTrackProb = 0.1,
                    tLims = [1, 12],
        		    xLims = [0.0, 255.0],
		            yLims = [0.0, 255.0])

trackerDefaults = dict( trackers = [],
                        corner_file = "corners",
		                inputDataFile = "InputDataFile",
		                result_file = "testResults",
                        trackerparams = "trackruns.ini",
                        analysis_stem = "resultAnalysis")

def Save_MultiSim_Params(filename, params) :
    SaveConfigFile(filename, params)

def SaveConfigFile(filename, params) :
    config = ConfigObj(params, interpolation=False)
    config.filename = filename
    config.write()

def SaveSimulationParams(simParamName, simParams) :
    config = ConfigObj(simParams, interpolation=False)
    #tLims = config.pop('tLims')
    #config['frameCnt'] = max(tLims) - min(tLims) + 1
    config.filename = simParamName
    config.write()

def ArgValidator(config) :
    for keyName in config :
        if keyName in ['seed', 'frameCnt', 'totalTracks'] :
            # Grab single integer
            config[keyName] = int(config[keyName])
        elif keyName in ['endTrackProb'] :
            # Grab single float
	        config[keyName] = float(config[keyName])
        elif keyName in ['xLims', 'yLims', 'tLims'] :
            # Grab array of floats, from a spliting by whitespace
            config[keyName] = map(float, config[keyName])

def Read_MultiSim_Params(filename) :
    if not (os.path.isfile(filename) and os.access(filename, os.R_OK)) :
        raise Exception("Can not find or read config file: %s" % filename)

    config = ConfigObj(filename, interpolation=False)

    vdtor = Validator()
    config.configspec = ConfigObj(dict(globalSeed="integer",
                                       simCnt="integer(min=0)",
                                       simName="string"),
                                  list_values=False,
                                  _inspec=True)
    res = config.validate(vdtor)
    flatErrs = flatten_errors(config, res)
    _ShowErrors(flatErrs)

    return config

def ReadSimulationParams(simParamName) :
    if not (os.path.isfile(simParamName) and os.access(simParamName, os.R_OK)):
        raise Exception("Can not find or read config file: %s" % simParamName)
    config = ConfigObj(simParamName, interpolation=False)

    vdtor = Validator()
    config.configspec = ConfigObj(dict(frameCnt="integer(min=1, default=%d)" % simDefaults['frameCnt'],
                                       totalTracks="integer(min=0, default=%d)" % simDefaults['totalTracks'],
                                       seed="integer(default=%d)" % simDefaults['seed'],
                                       simTrackFile="string(default=%s)" % simDefaults['simTrackFile'],
                                       noisyTrackFile="string(default=%s)" % simDefaults['noisyTrackFile'],
                                       simConfFile="string(default=%s)" % simDefaults['simConfFile'],
                                       endTrackProb="float(min=0.0, max=1.0, default=%f)" % simDefaults['endTrackProb'],
                                       tLims="float_list(min=2, max=2, default=list(%f, %f))" % tuple(simDefaults['tLims']),
                                       xLims="float_list(min=2, max=2, default=list(%f, %f))" % tuple(simDefaults['xLims']),
                                       yLims="float_list(min=2, max=2, default=list(%f, %f))" % tuple(simDefaults['yLims']),

                                       trackers="force_list()",
                                       corner_file="string(default=%s)" % trackerDefaults['corner_file'],
                                       inputDataFile = "string(default=%s)" % trackerDefaults['inputDataFile'],
                                       result_file = "string(default=%s)" % trackerDefaults['result_file'],
                                       trackerparams="string(default=%s)" % trackerDefaults['trackerparams'],
                                       analysis_stem="string(default=%s)" % trackerDefaults['analysis_stem']),
                                 list_values=False,
                                 _inspec=True)
    
    #ArgValidator(config)

    #simParams = simDefaults.copy()
    #simParams.update(trackerDefaults)
    #simParams.update(config)

    #frameCnt = simParams.pop('frameCnt')
    #simParams['tLims'] = (1, frameCnt)
    res = config.validate(vdtor, preserve_errors=True)
    flatErrs = flatten_errors(config, res)
    _ShowErrors(flatErrs)

    return config

def _ShowErrors(flatErrs, skipMissing=False) :
    hasErrs = False
    for (section_list, key, error) in flatErrs :
        isErr = False
        if key is not None :
            isErr = True
            section_list.append(key)
        elif skipMissing is False :
            isErr = True
            section_list.append('[missing key/section]')
        section_string = ', '.join(section_list)
        if error == False :
            error = 'Missing value or section.'

        if isErr :
            hasErrs = True
            print section_string, ' = ', error
        
    if hasErrs :
        # TODO: Make an exception class for errors in reading param files
        raise Exception("Invalid data in configuration")

def LoadTrackerParams(filenames, trackers=None) :
    trackConfs = ConfigObj(interpolation=False)
    for name in filenames :
        if not (os.path.isfile(name) and os.access(name, os.R_OK)) :
            raise Exception("Can not find or read config file: %s" % name)
        partConf = ConfigObj(name, interpolation=False)
        trackConfs.merge(partConf)

    configSpec = {}
    # Building the config spec for the tracker parameters
    # This data comes from the registration info that each Tracker provides.
    for aTrackRun in trackConfs.keys() :
        algo = trackConfs[aTrackRun]['algorithm']
        configSpec[aTrackRun] = param_confList[algo]

    vdtor = Validator()
    trackConfs.configspec = ConfigObj(configSpec, list_values=False, _inspec=True)
    res = trackConfs.validate(vdtor, preserve_errors=True)
    flatErrs = flatten_errors(trackConfs, res)
    _ShowErrors(flatErrs)

    if trackers is not None :
        raise NotImplementedError("Selecting trackers have not been implemented yet...")

    return trackConfs


def LoadSimulatorConf(filenames) :
    simConfs = ConfigObj()
    for name in filenames :
        if not (os.path.isfile(name) and os.access(name, os.R_OK)) :
            raise Exception("Can not find or read config file: %s" % name)
        partConf = ConfigObj(name)
        simConfs.merge(partConf)

    headerList = [('InitModels', init_modelList),
                  ('MotionModels', motion_modelList),
                  ('TrackGens', gen_modelList),
                  ('NoiseModels', noise_modelList)]

    configSpec = {}
    # Building the config spec for the InitModels, MotionModels, TrackGens
    # and NoiseModels sections.  This data comes from the registration info
    # that each class provides.
    for name, modelList in headerList :
        configSpec[name] = {}
        # TODO: turn this into a dict comprehension
        for key in simConfs[name] :
            theType = simConfs[name][key].get('type')
            configSpec[name][key] = modelList[theType][1]

    # Lastly, adding the config spec for the SimModels section.
    configSpec['SimModels'] = {'__many__' : dict(prob_track_ends="float(min=0, max=1)",
                                                 maxTrackLen="integer(min=0)",
                                                 cnt="integer(min=0)",
                                                 noises="force_list()")}
    vdtor = Validator()
    simConfs.configspec = ConfigObj(configSpec, list_values=False, _inspec=True)

    res = simConfs.validate(vdtor)
    flatErrs = flatten_errors(simConfs, res)
    _ShowErrors(flatErrs, skipMissing=True)

    return simConfs

def SetupParser(parser) :
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

    group.add_argument("--seed", dest="seed", type=int,
		     help="Initialize RNG with SEED. (default: %(default)s)",
		     metavar="SEED", default = simDefaults['seed'])

    
    group.add_argument("--simconffile", dest="simConfFile", type=str,
		     help="Save simulation conf to FILE. (default: %(default)s)", 
		     metavar="FILE",
		     default=simDefaults['simConfFile'])


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

    group.add_argument("--xlims", dest="xLims", type=float,
		     nargs = 2,
		     help="Domain limits in x-axis. (default: %(default)s)", 
		     metavar="X", default=simDefaults['xLims'])

    group.add_argument("--ylims", dest="yLims", type=float,
		     nargs = 2,
		     help="Domain limits in y-axis. (default: %(default)s)", 
		     metavar="Y", default=simDefaults['yLims'])

    group.add_argument("--tlims", dest="tLims", type=float,
             nargs = 2,
             help="Domain limits in t-axis. (default: %(default)s)",
             metavar="T", default=simDefaults['tLims'])

    return group



def TrackerGroup(parser) :
    group = parser.add_argument_group("Tracker Options",
                        "Options for controlling the input and output of the trackers.")

    # Commenting this out for now because I think I want this to be
    # controled by the Tracking programs to update the parameters on
    # which trackers were used.
#    group.add_argument("-t", "--tracker", dest="trackers", type=str,
#		     action="append",
#                     help="Tracking models to use. (Ex: MHT, SCIT)",
#                     metavar="TRACKER", default = trackerDefaults['trackers'])

    group.add_argument("--corner", dest="corner_file", type=str,
		     help="Corner filename stem. (default = %(default)s)",
		     metavar="CORNER", default = trackerDefaults['corner_file'])

    group.add_argument("--input", dest="inputDataFile", type=str,
		     help="MHT's Input datafile. (default = %(default)s)",
		     metavar="FILE", default = trackerDefaults['inputDataFile'])

    group.add_argument("--result", dest="result_file", type=str,
		     help="Tracker filename stem for results. (default = %(default)s)",
		     metavar="RESULT", default=trackerDefaults['result_file'])

    group.add_argument("--paramstore", dest="trackerparams", type=str,
                       help="Filename to use for storing the parameters for each trackrun. (default = %(default)s)",
                       metavar="FILE", default=trackerDefaults['trackerparams'])

    group.add_argument("--analysis", dest="analysis_stem", type=str,
                       help="Filename stem for the analysis of track run results. (default = %(default)s)",
                       metavar="ANALYSIS", default=trackerDefaults['analysis_stem'])

    return group



def ParamsFromOptions(options, simName = None) :
    # NOTE: Couldn't I now use the ConfigObj loader to do this validation?
    # NOTE: I do NOT modify the contents of the
    #       options object! This is important for
    #       reusability within a multi-simulation program.
    #       Treat options like a const.
    if simName is None : simName = options.simName

    # Error checking
    if options.frameCnt <= 0 :
        parser.error("ERROR: Invalid FrameCnt value: %d" % (options.frameCnt))

    if options.totalTracks < 0 :
        parser.error("ERROR: Invalid TrackCnt value: %d" % (options.totalTracks))

    if options.endTrackProb < 0. :
        parser.error("ERROR: End Track Prob must be positive! Value: %d" % (options.endTrackProb))

    # TODO: Maybe this can be turned into a dict comprehension?
    return dict(corner_file = options.corner_file,
		inputDataFile = options.inputDataFile,
		result_file = options.result_file,
        trackerparams = options.trackerparams,
        analysis_stem = options.analysis_stem,
        simTrackFile = options.simTrackFile,
		noisyTrackFile = options.noisyTrackFile,
        simConfFile = options.simConfFile,
        simName = simName,
        # Commenting this out for now to examine the possibility
        # of internally handling this value, so we will set
        # it to an empty list for now.
		#trackers = options.trackers,
        trackers = [],
        totalTracks = options.totalTracks,
        endTrackProb = options.endTrackProb,
        frameCnt = options.frameCnt,
        xLims = options.xLims,
        yLims = options.yLims,
		tLims = options.tLims,
        seed = options.seed
        ) 


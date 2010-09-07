import os
import argparse
from configobj import ConfigObj
from Sim import gen_modelList, noise_modelList, motion_modelList, init_modelList
from validate import Validator

simDefaults = dict( frameCnt = 12,
	            totalTracks = 30,
		    seed = 42,
		    simTrackFile = "true_tracks",
		    noisyTrackFile = "noise_tracks",
            simConfFile = "simulation.ini",
		    endTrackProb = 0.1,
		    xLims = [0.0, 255.0],
		    yLims = [0.0, 255.0])

trackerDefaults = dict(trackers = ['SCIT'],
		       corner_file = "corners",
		       inputDataFile = "InputDataFile",
		       result_file = "testResults")

def Save_MultiSim_Params(filename, params) :
    SaveConfigFile(filename, params)

def SaveConfigFile(filename, params) :
    config = ConfigObj(params, interpolation=False)
    config.filename = filename
    config.write()

def SaveSimulationParams(simParamName, simParams) :
    config = ConfigObj(simParams, interpolation=False)
    tLims = config.pop('tLims')
    config['frameCnt'] = max(tLims) - min(tLims) + 1
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
        elif keyName in ['xLims', 'yLims'] :
            # Grab array of floats, from a spliting by whitespace
            config[keyName] = map(float, config[keyName])

def Read_MultiSim_Params(filename) :
    config = ConfigObj(filename, interpolation=False)

    vdtor = Validator()
    config.configspec = ConfigObj(dict(globalSeed="int",
                                       simCnt="int(min=0)",
                                       simName="str"),
                                  list_values=False,
                                  _inspec=True)
    config.validate(vdtor)

    return config

def ReadSimulationParams(simParamName) :
    config = ConfigObj(simParamName, interpolation=False)
    
    ArgValidator(config)

    simParams = simDefaults.copy()
    simParams.update(trackerDefaults)
    simParams.update(config)

    frameCnt = simParams.pop('frameCnt')
    simParams['tLims'] = (1, frameCnt)
    return simParams

def LoadTrackerParams(filenames, simParams, trackers=None) :
    trackConfs = ConfigObj(interpolation=False)
    for name in filenames :
        partConf = ConfigObj(name, interpolation=False)
        trackConfs.merge(partConf)

    def fakeinterp(section, key, **simParams) :
        val = section[key]
        if isinstance(val, str) :
            section[key] = val % simParams
    
    trackConfs.walk(fakeinterp,  call_on_sections=False, **simParams)

    if trackers is not None :
        raise NotImplementedError("Selecting trackers have not been implemented yet...")

    return trackConfs


def LoadSimulatorConf(filenames) :
    simConfs = ConfigObj()
    for name in filenames :
        partConf = ConfigObj(name)
        simConfs.merge(partConf)

    headerList = [('InitModels', init_modelList),
                  ('MotionModels', motion_modelList),
                  ('TrackGens', gen_modelList),
                  ('NoiseModels', noise_modelList)]

    configSpec = {}
    for name, modelList in headerList :
        configSpec[name] = {}
        for key in simConfs[name] :
            theType = simConfs[name][key].get('type')
            configSpec[name][key] = modelList[theType][1]

    configSpec['SimModels'] = {'__many__' : dict(prob_track_ends="float(0, 1)",
                                                 maxTrackLen="integer(min=0)",
                                                 cnt="integer(min=0)",
                                                 noises="force_list")}
    vdtor = Validator()
    simConfs.configspec = ConfigObj(configSpec, list_values=False, _inspec=True)

    # TODO: Error routines...
    simConfs.validate(vdtor)

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

    if options.endTrackProb < 0. :
        parser.error("ERROR: End Track Prob must be positive! Value: %d" % (options.endTrackProb))

    return dict(corner_file = options.corner_file,
		inputDataFile = options.inputDataFile,
		result_file = options.result_file,
        simTrackFile = options.simTrackFile,
		noisyTrackFile = options.noisyTrackFile,
        simConfFile = options.simConfFile,
        simName = simName,
		trackers = options.trackers,
        totalTracks = options.totalTracks,
        endTrackProb = options.endTrackProb,
        xLims = options.xLims,
        yLims = options.yLims,
		tLims = (1, options.frameCnt),
        seed = options.seed
        ) 


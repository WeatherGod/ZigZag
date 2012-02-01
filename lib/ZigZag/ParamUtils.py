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
                    simTagFile = "simTags.ini",
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
    config.filename = simParamName
    if config.get('times', None) is None :
        config.pop('times', None)
    config.write()


def ReadConfigFile(filename) :
    if not (os.path.isfile(filename) and os.access(filename, os.R_OK)) :
        raise Exception("Can not find or read config file: %s" % filename)

    return ConfigObj(filename, interpolation=False)

def _recurse_find(tags, name) :
    res = None

    for section in tags.sections :
        if section == name :
            return tags[section]['ids']
        else :
            res = _recurse_find(tags[section], name)
            if res is not None :
                return res

    return res

def _find_names(conf) :
    names = []
    for sect in conf.sections :
        names.extend(_find_names(conf[sect]))
    names.extend(conf.sections)

    return names

def process_tag_filters(simTags, filters) :
    if filters is None or simTags is None :
        return None

    # Split the list into "includes" and "excludes" based on the
    # presence of a '+' or '-' sign at the end of each tagname.
    in_tags = [name[:-1] for name in filters if name[-1] == '+']
    ex_tags = [name[:-1] for name in filters if name[-1] == '-']

    keepers = set()



    if len(in_tags) == 0 :
        # Assume we mean that we want all of the generators
        in_tags = _find_names(simTags)

    for name in in_tags :
        ids = _recurse_find(simTags, name)
        if ids is None :
            raise ValueError("%s is not in the simTags" % name)
        keepers.update(ids)

    for name in ex_tags :
        ids = _recurse_find(simTags, name)
        if ids is None :
            raise ValueError("%s is not in the simTags" % name)
        keepers.difference_update(ids)

    return keepers


def ReadSimTagFile(filename) :
    if not os.path.exists(filename) :
        # For compatibility with scenarios and simulations that have no tags
        # This is not a backwards-compatibility issue because a scenario is
        # not required to have a simTag file.
        return None

    conf = ReadConfigFile(filename)
    def _make_spec(sect, key) :
        return 'int_list()'

    confSpec = conf.walk(_make_spec)
    return ConfValidation(conf, confSpec)

def Read_MultiSim_Params(filename) :
    config = ReadConfigFile(filename)

    configSpec = dict(globalSeed="integer",
                      simCnt="integer(min=0)",
                      simName="string")
    return ConfValidation(config, configSpec)

def ReadSimulationParams(simParamName) :
    config = ReadConfigFile(simParamName)

    if config.get('times', None) == 'None' :
        config.pop('times', None)

    configSpec = dict(
             frameCnt="integer(min=1, default=%d)" % simDefaults['frameCnt'],
             totalTracks="integer(min=0, default=%d)" %
                                                 simDefaults['totalTracks'],
             seed="integer(default=%d)" % simDefaults['seed'],
             simTrackFile="string(default=%s)" % simDefaults['simTrackFile'],
             noisyTrackFile="string(default=%s)" %
                                                 simDefaults['noisyTrackFile'],
             simConfFile="string(default=%s)" % simDefaults['simConfFile'],
             simTagFile="string(default=%s)" % simDefaults['simTagFile'],
             endTrackProb="float(min=0.0, max=1.0, default=%f)" %
                                                 simDefaults['endTrackProb'],
             tLims="float_list(min=2, max=2, default=list(%f, %f))" %
                                                 tuple(simDefaults['tLims']),
             xLims="float_list(min=2, max=2, default=list(%f, %f))" %
                                                 tuple(simDefaults['xLims']),
             yLims="float_list(min=2, max=2, default=list(%f, %f))" %
                                                 tuple(simDefaults['yLims']),

             trackers="force_list()",
             corner_file="string(default=%s)" % trackerDefaults['corner_file'],
             inputDataFile = "string(default=%s)" %
                                            trackerDefaults['inputDataFile'],
             result_file = "string(default=%s)" %
                                            trackerDefaults['result_file'],
             trackerparams="string(default=%s)" %
                                            trackerDefaults['trackerparams'],
             analysis_stem="string(default=%s)" %
                                            trackerDefaults['analysis_stem'],
             times="float_list(default=None)")

    return ConfValidation(config, configSpec)

def _ShowErrors(flatErrs, skipMissing=False) :
    errmsgs = []
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
            errmsgs.append(section_string + ' = ' + str(error))
        
    if len(errmsgs) > 0 :
        # TODO: Make an exception class for errors in reading param files
        raise Exception("Invalid data in configuration:\n" +
                        "\n".join(errmsgs))

def LoadTrackerParams(filenames, trackers=None) :
    trackConfs = ConfigObj(interpolation=False)
    for name in filenames :
        partConf = ReadConfigFile(name)
        trackConfs.merge(partConf)

    configSpec = {}
    # Building the config spec for the tracker parameters
    # This data comes from the registration info that each Tracker provides.
    for aTrackRun in trackConfs.keys() :
        algo = trackConfs[aTrackRun]['algorithm']
        configSpec[aTrackRun] = param_confList[algo]


    trackConfs = ConfValidation(trackConfs, configSpec)

    if trackers is not None :
        raise NotImplementedError("Selecting trackers have not been"
                                  " implemented yet...")

    return trackConfs


def LoadSimulatorConf(filenames) :
    simConfs = ConfigObj()
    for name in filenames :
        partConf = ReadConfigFile(name)
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
    configSpec['SimModels'] = {'__many__' :
                                 dict(prob_track_ends="float(min=0, max=1)",
                                      maxTrackLen="integer(min=0)",
                                      cnt="integer(min=0)",
                                      noises="force_list()")}

    return ConfValidation(simConfs, configSpec)

def ConfValidation(confs, configSpec) :
    vdtor = Validator()
    confs.configspec = ConfigObj(configSpec, list_values=False, _inspec=True)

    res = confs.validate(vdtor)
    flatErrs = flatten_errors(confs, res)
    _ShowErrors(flatErrs, skipMissing=True)

    return confs

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

    group.add_argument("--tagfile", dest="simTagFile", type=str,
             help="Output cornerIDs to FILE for tagging."
                  " (default: %(default)s)",
             metavar="FILE", default=simDefaults['simTagFile'])

    group.add_argument("--trackend", dest="endTrackProb", type=float,
		     help="Probability a track will end for a given frame."
                  " (default: %(default)s)",
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
                       help="Filename to use for storing the parameters"
                            " for each trackrun. (default = %(default)s)",
                       metavar="FILE", default=trackerDefaults['trackerparams'])

    group.add_argument("--analysis", dest="analysis_stem", type=str,
                       help="Filename stem for the analysis of track run"
                            " results. (default = %(default)s)",
                       metavar="ANALYSIS",
                       default=trackerDefaults['analysis_stem'])

    return group



def ParamsFromOptions(options, simName=None) :
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
        parser.error("ERROR: Invalid TrackCnt"
                     " value: %d" % (options.totalTracks))

    if options.endTrackProb < 0. :
        parser.error("ERROR: End Track Prob must be"
                     " positive! Value: %d" % (options.endTrackProb))

    # TODO: Maybe this can be turned into a dict comprehension?
    return dict(corner_file = options.corner_file,
		inputDataFile = options.inputDataFile,
		result_file = options.result_file,
        trackerparams = options.trackerparams,
        analysis_stem = options.analysis_stem,
        simTrackFile = options.simTrackFile,
		noisyTrackFile = options.noisyTrackFile,
        simConfFile = options.simConfFile,
        simTagFile = options.simTagFile,
        simName = simName,
        trackers = [],
        totalTracks = options.totalTracks,
        endTrackProb = options.endTrackProb,
        frameCnt = options.frameCnt,
        xLims = options.xLims,
        yLims = options.yLims,
		tLims = options.tLims,
        seed = options.seed
        ) 


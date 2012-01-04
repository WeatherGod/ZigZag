
_zigargs = {}
_common_args = {}

def AddCommandParser(command, parser) :
    if command not in _zigargs :
        raise ValueError("The command '%s' is not registered." % command)

    for args in _zigargs[command] :
        if isinstance(args, str) :
            parser.add_argument(*_common_args[args][0],
                                **_common_args[args][1])
        else :
            parser.add_argument(*args[0], **args[1])


_common_args["simName"] = (("simName",),
        dict(help="Tracks for SIMNAME",
             metavar="SIMNAME", default="NewSim"))
_common_args["simNames"] = (("simNames",),
        dict(help="Tracks for SIMNAME",
             nargs='+',
             metavar="SIMNAME", type=str))

_common_args["multiSim"] = (("multiSim",), 
        dict(type=str,
             help="Tracks for multiple realizations from MULTISIM",
             metavar="MULTISIM", default="NewMulti"))
_common_args["multiSims"] = (("multiSims",),  
        dict(help="Tracks for multiple realizations from MULTISIMs",
             nargs='+',
             metavar="MULTISIM", type=str))

_common_args["simCnt"] = (("simCnt",), 
        dict(type=int,
             help="Repeat Simulation N times.",
             metavar="N", default=1))
_common_args["trackconfs"] = (("trackconfs",), 
        dict(nargs='+',
             help="Config files for the parameters for the trackers",
             metavar="CONF"))
_common_args["skillNames"] = (("skillNames",), 
        dict(nargs="+",
             help="The skill measures to use (e.g., HSS)",
             metavar="SKILL"))

_common_args["-d"] = (("-d", "--dir"),
        dict(dest="directory", help="Base directory for SIMNAME/MULTISIM",
             metavar="DIRNAME", default='.'))
_common_args["-c"] = (("-c", "--conf"), 
        dict(dest="simConfFiles",
             nargs='+',
             help="Configuration files for the simulation.",
             metavar="CONFFILE", default=None))
_common_args["-t"] = (("-t", "--trackruns"),
        dict(dest="trackRuns",
             nargs="+", help="RUNs to use. If none are given, use all RUNs"
                             " listed in CONF",
             metavar="RUN", default=None))
_common_args["-s"] = (("-s", "--skills"),
        dict(dest='skillNames', nargs="+",
             help="The skill measures to use (e.g., HSS)",
             metavar="SKILL"))



_zigargs['TrackSim'] = ["simName", "-d", "-c"]
_zigargs['MultiSim'] = ["multiSim", "simCnt", "-d", "-c"]
_zigargs['DownsampleSim'] = ["simName",
    (("newName",), 
     dict(help="Name of the new simulation",
          metavar="NEWNAME")),
    (("skipCnt",), 
     dict(type=int,
          help="Skip CNT frames for downsampling",
          metavar="CNT")),
    (("--volume",),
     dict(dest="doTracks",
          action="store_false",
          help="Downsample only the corner files, not tracks",
          default=True)),
    "-d"
    ]

_zigargs['MultiDownsample'] = ["multiSim",
    (("newName",), 
     dict(help="Name of the downsampled multi-sim",
          metavar="NEWMULTI")),
    (("skipCnt",), 
     dict(type=int,
          help="Skip CNT frames for downsampling",
          metavar="CNT")),
#    (("--volume",),
#     dict(dest="doTracks",
#          action="store_false",
#          help="Downsample only the corner files, not tracks",
#          default=True)),
    "-d"
    ]

_zigargs['DoTracking'] = ["simName", "trackconfs", "-t", "-d"]
_zigargs['MultiTracking'] = ["multiSim", "trackconfs", "-t", "-d"]
_zigargs['AnalyzeTracking'] = ["simName", "-t", "-d",
    (("--cache",), 
     dict(dest="cacheOnly",
          help="Only bother with processing for the purpose"
               " of caching results.",
          action="store_true", default=False)),
    ]

_zigargs['MultiAnalysis'] = ["multiSim", "skillNames", "-t",
    (("--titles",),
     dict(dest="titles",
          nargs="+", help="Titles for the plots.  Default is to use the"
                          " skill score name",
          metavar="TITLE", default=None)),
    (("--ticklabels",),
     dict(dest="ticklabels",
          nargs="+", help="Tick labels.  Default is to use the run names.",
          metavar="LABEL", default=None)),


    (("--cache",),
     dict(dest="cacheOnly",
          help="Only bother with processing for the purpose of"
               " caching results.",
          action="store_true", default=False)),
    "-d",

    (("--compare",), 
     dict(dest="compareTo", type=str,
          help="Compare other trackers to TRACKER",
          metavar="TRACKER", default="MHT")),
    (("--find_best",), 
     dict(dest="doFindBest", action="store_true",
          help="Find the best comparisons.", default=False)),
    (("--find_worst",), 
     dict(dest="doFindWorst", action = "store_true",
          help="Find the Worst comparisons.", default=False)),

    (("--save",), 
     dict(dest="saveImgFile", type=str,
          help="Save the resulting image using FILESTEM as the prefix."
               " (e.g., saved file will be 'foo/bar_PC.png' for the PC"
               " skill scores and suffix of 'foo/bar').  Use --type to"
               " control which image format.",
          metavar="FILESTEM", default=None)),
    (("--type",), 
     dict(dest="imageType", type=str,
          help="Image format to use for saving the figures."
               " Default: %(default)s",
          metavar="TYPE", default='png')),
    (("-f", "--figsize"), 
     dict(dest="figsize", type=float,
          nargs=2, help="Size of the figure in inches (width x height)."
                        " Default: %(default)s",
          metavar="SIZE", default=(11.0, 5.0))),
    (("--noshow",), 
     dict(dest="doShow", action = 'store_false',
          help="To display or not to display...",
          default=True))
    ]

_zigargs['MultiScenarioAnalysis'] = ["multiSims", "-s", "-t",
    (("--titles",),
     dict(dest="titles",
          nargs="+", help="Titles for the plots.  Default is to use the"
                          " skill score name",
          metavar="TITLE", default=None)),
    (("--ticklabels",),
     dict(dest="ticklabels",
          nargs="+", help="Tick labels.  Default is to use the sim names",
          metavar="LABEL", default=None)),

    (("--plotlabels",),
     dict(dest="plotlabels",
          nargs="+", help="TrackRun Labels.  Default is to use the run names",
          metavar="LABEL", default=None)),

    (("--cache",), 
     dict(dest="cacheOnly",
          help="Only bother with processing for the purpose of caching results.",
          action="store_true", default=False)),
    "-d",

    (("--save",), 
     dict(dest="saveImgFile", type=str,
          help="Save the resulting image using FILESTEM as the prefix. (e.g., saved file will be 'foo/bar_PC.png' for the PC skill scores and suffix of 'foo/bar').  Use --type to control which image format.",
          metavar="FILESTEM", default=None)),
    (("--type",), 
     dict(dest="imageType", type=str,
          help="Image format to use for saving the figures. Default: %(default)s",
          metavar="TYPE", default='png')),
    (("-f", "--figsize"), 
     dict(dest="figsize", type=float,
          nargs=2, help="Size of the figure in inches (width x height). Default: %(default)s",
          metavar="SIZE", default=(11.0, 5.0))),
    (("--noshow",), 
     dict(dest="doShow", action = 'store_false',
          help="To display or not to display...",
          default=True))
    ]

_zigargs['ListRuns'] = ["simNames",
    (("-f", "--files"),
     dict(action='store_true', dest='listfiles',
          help="Do we list the track runs, or the track result files?"
               " (Default is to list the runs)",
          default=False)),
    "-t",
    (("-m", "--multi"), 
     dict(dest='isMulti',
          help="Indicate that SIMNAME(s) is actually a Multi-Sim so that"
               " we can process correctly.",
          default=False, action='store_true')),
    "-d"
    ]

_zigargs['MoveRuns'] = ["simNames",
    (("-o", "--old"),
     dict(dest="old",
          help="The pattern to match",
          metavar="OLD", default=None)),
    (("-n", "--new"),
     dict(dest="new",
          help="The string to replace the OLD pattern with.",
          metavar="NEW", default=None)),
    "-t",
    (("-m", "--multi"), 
     dict(dest='isMulti',
          help="Indicate that SIMNAME(s) is actually a Multi-Sim"
               " so that we can process correctly.",
          default=False, action='store_true')),
    "-d" 
    ]

_zigargs['ParamSearch'] = [
    (("paramFile",), 
     dict(help="The configuration file", metavar="FILE")),
    (("tracker",), 
     dict(help="The tracker algorithm to use", metavar="TRACKER")),
    (("-p", "--param"), 
     dict(dest="parameters", type=str,
          help="Name of parameter", action="append",
          metavar="NAME", default=[])),
    (("--silent",), 
     dict(dest="silentParams", type=str,
          help="Parameters not to include in the name of the track runs",
          metavar="NAME", nargs='+', default=[])),
    (("-i", "--int"), 
     dict(dest="paramSpecs", type=int,
          help="Scalar integer parameter value", action="append",
          metavar="VAL")),
    (("-f", "--float"), 
     dict(dest="paramSpecs", type=float,
          help="Scalar float parameter value", action="append",
          metavar="VAL")),
    (("-s", "--str"), 
     dict(dest="paramSpecs", type=str,
          help="Scalar str parameter value", action="append",
          metavar="VAL")),
    (("-b", "--bool"), 
     dict(dest="paramSpecs", type=bool,
          help="Scalar bool parameter value", action="append",
          metavar="VAL")),
    (("--lint",), 
     dict(dest="paramSpecs", nargs='+', type=int,
          help="Integer list parameter value", action="append",
          metavar="VAL")),
    (("--lfloat",), 
     dict(dest="paramSpecs", nargs='+', type=float,
          help="Float list parameter value", action="append",
          metavar="VAL")),
    (("--lstr",), 
     dict(dest="paramSpecs", nargs='+', type=str,
          help="String list parameter value", action="append",
          metavar="VAL")),
    (("--lbool",), 
     dict(dest="paramSpecs", nargs='+', type=bool,
          help="String list parameter value", action="append",
          metavar="VAL")),

    (("--range",), 
     dict(dest="paramSpecs", nargs='+', type=int,
          help="Integer list created by range()", action='AppendRange',
          metavar="VAL")),
    (("--arange",), 
     dict(dest="paramSpecs", nargs='+', type=float,
          help="Float list created by numpy.arange()", action='AppendARange',
          metavar="VAL")),
    (("--linspace",), 
     dict(dest="paramSpecs", nargs='+', type=float,
          help="Float list created by numpy.linspace()",
          action='AppendLinspace',
          metavar="VAL")),
    (("--logspace",), 
     dict(dest="paramSpecs", nargs='+', type=float,
          help="Float list created by numpy.logspace()",
          action='AppendLogspace',
          metavar="VAL"))
    ]

show_opts = [
    (("--titles",),
     dict(dest='trackTitles', type=str,
          nargs='+', help=("Titles to use for the figure subplots. "
                           "Default is to use the filenames."),
          metavar="TITLE", default=None)),

    (("--save",),
     dict(dest="saveImgFile",
          help="Save the resulting image as FILENAME.",
          metavar="FILENAME", default=None)),
    (("--noshow",),
     dict(dest="doShow", action = 'store_false',
          help="To display or not to display...",
          default=True)),
    (("-l", "--layout"),
     dict(dest="layout", type=int,
          nargs=2, help=("Layout of the subplots (rows x columns). "
                         "All plots on one row by default."),
          metavar="NUM", default=None)),
    (("-f", "--figsize"),
     dict(dest="figsize", type=float,
          nargs=2, help="Size of the figure in inches (width x height)."
                        " Default: auto",
          metavar="SIZE", default=None)),
    ]

map_opts = [
    (("--station",),
     dict(dest="statLonLat", type=float,
          nargs=2, help=("LON LAT of the origin (0, 0) of the track data. "
                         " When specified, the domain will change to"
                         " Longitude and Latitude, and map layers can be"
                         " displayed with '-m' switch."),
          metavar="COORDS", default=None)),
    (("-m", "--map"),
     dict(dest="displayMap",
          action="store_true", help=("Turn on display of map layers."
                                     " Only valid with '--station' option."),
          default=False))
    ]



_zigargs['ShowTracks2'] = [
    (("trackFiles",),
     dict(nargs='+',
          help="TRACKFILEs to use for display",
          metavar="TRACKFILE")),
    ] + show_opts + map_opts


_zigargs['ShowCompare2'] = [
    (("trackFiles",),
     dict(nargs='+',
          help="TRACKFILEs to use for display",
          metavar="TRACKFILE")),
    (("-t", "--truth"),
     dict(dest="truthTrackFile", nargs='+',
          help="Use TRUTHFILE for true track data",
          metavar="TRUTHFILE")),
    ] + show_opts + map_opts

_zigargs['ShowCorners2'] = [
    (("inputDataFiles",),
     dict(nargs='+',
          help="Use INDATAFILE for finding corner data files",
          metavar="INDATAFILE")),
    (("--tail",),
     dict(dest='tail', type=int,
          help="Length of lagging tail in frames. Default depends on"
               " the program.",
          metavar='N', default=None)),
    ] + show_opts + map_opts

_zigargs['ShowTracks'] = [
    (("trackFiles",),
     dict(nargs='*',
          help="TRACKFILEs to use for display",
          metavar="TRACKFILE", default=[])),
    (("-t", "--truth"),
     dict(dest="truthTrackFile",
          help="Use TRUTHFILE for true track data",
          metavar="TRUTHFILE", default=None)),
    (("-r", "--trackruns"),
     dict(dest="trackRuns",
          nargs="+", help="Trackruns to analyze.  Analyze all runs "
                          " if none are given",
          metavar="RUN", default=None)),
    (("-s", "--simName"),
     dict(dest="simName",
          help="Use data from the simulation SIMNAME",
          metavar="SIMNAME", default=None)),
    "-d"
    ] + show_opts + map_opts


_zigargs['ShowAnims'] = [
    (("trackFiles",),
     dict(nargs='*',
          help="TRACKFILEs to use for display",
          metavar="TRACKFILE", default=[])),
    (("-t", "--truth"), 
     dict(dest="truthTrackFile",
          help="Use TRUTHFILE for true track data",
          metavar="TRUTHFILE", default=None)),
    (("-r", "--trackruns"), 
     dict(dest="trackRuns",
          nargs="+", help="Trackruns to analyze.  Analyze all runs if"
                          " none are given",
          metavar="RUN", default=None)),
    (("-s", "--simName"), 
     dict(dest="simName",
          help="Use data from the simulation SIMNAME",
          metavar="SIMNAME", default=None)),
    "-d",
    (("--tail",),
     dict(dest='tail', type=int,
          help="Length of lagging tail in frames. Default depends on"
               " the program.",
          metavar='N', default=None)),
    ] + show_opts + map_opts

_zigargs['ShowCorners'] = [
    (("inputDataFiles",), 
     dict(nargs='*',
          help="Use INDATAFILE for finding corner data files",
          metavar="INDATAFILE")),
    (("-t", "--track"), 
     dict(dest="trackFile",
          help="Use TRACKFILE for determining domain limits.",
          metavar="TRACKFILE", default=None)),

    (("-s", "--simName"), 
     dict(dest="simName",
          help="Use data from the simulation SIMNAME.",
          metavar="SIMNAME", default=None)),
    "-d",
    (("--tail",),
     dict(dest='tail', type=int,
          help="Length of lagging tail in frames. Default depends on"
               " the program.",
          metavar='N', default=None)),
    ] + show_opts + map_opts


_zigargs['TrackReports'] = [
    (("trackfiles",),
     dict(nargs='+', type=str,
          help='Analyze the tracks in FILE.',
          metavar='FILE')),
    ]


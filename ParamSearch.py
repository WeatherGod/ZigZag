#!/usr/bin/env python

from MultiAnalysis import MultiAnalyze
from MultiTracking import MultiTrack

import numpy as np




if __name__ == '__main__' :
    import argparse
    import os           # for os.sep
    from configobj import ConfigObj

    # --------------------------------------------
    #  Functions and Argument Action classes for advanced handling
    # of this program's command-line options.
    #
    def ListAppend(namespace, destName, theList) :
        theAttr = getattr(namespace, destName)
        if theAttr is None :
            # That attribute hasn't been made yet, so make it!
            setattr(namespace, destName, [theList])
        else :
            theAttr.append(theList)
            

    class AppendRange(argparse.Action) :
        def __call__(self, parser, namespace, values, option_string=None) :
            ListAppend(namespace, self.dest, range(*values))


    class AppendARange(argparse.Action) :
        def __call__(self, parser, namespace, values, option_string=None) :
            ListAppend(namespace, self.dest, np.arange(*values))

    
    class AppendLinspace(argparse.Action) :
        def __call__(self, parser, namespace, values, option_string=None) :
            ListAppend(namespace, self.dest, np.linspace(*values))

    class AppendLogspace(argparse.Action) :
        def __call__(self, parser, namespace, values, option_string=None) :
            ListAppend(namespace, self.dest, np.logspace(*values))
    #
    # ---------------------------------------------------------------

    parser = argparse.ArgumentParser(description='Search for optimal parameters for a tracker for a given multi-sim')
    parser.add_argument("paramFile", help="The configuration file", metavar="FILE")
    parser.add_argument("tracker", help="The tracker algorithm to use", metavar="TRACKER")
    parser.add_argument("-p", "--param", dest="parameters", type=str,
                        help="Name of parameter", action="append",
                        metavar="NAME", default=[])
    parser.add_argument("--silent", dest="silentParams", type=str,
                        help="Parameters not to include in the name of the track runs",
                        metavar="NAME", nargs='+', default=[])
    parser.add_argument("-i", "--int", dest="paramSpecs", type=int,
                        help="Scalar integer parameter value", action="append",
                        metavar="VAL")
    parser.add_argument("-f", "--float", dest="paramSpecs", type=float,
                        help="Scalar float parameter value", action="append",
                        metavar="VAL")
    parser.add_argument("-s", "--str", dest="paramSpecs", type=str,
                        help="Scalar str parameter value", action="append",
                        metavar="VAL")
    parser.add_argument("-b", "--bool", dest="paramSpecs", type=bool,
                        help="Scalar bool parameter value", action="append",
                        metavar="VAL")



    parser.add_argument("--lint", dest="paramSpecs", nargs='+', type=int,
                        help="Integer list parameter value", action="append",
                        metavar="VAL")
    parser.add_argument("--lfloat", dest="paramSpecs", nargs='+', type=float,
                        help="Float list parameter value", action="append",
                        metavar="VAL")
    parser.add_argument("--lstr", dest="paramSpecs", nargs='+', type=str,
                        help="String list parameter value", action="append",
                        metavar="VAL")
    parser.add_argument("--lbool", dest="paramSpecs", nargs='+', type=bool,
                        help="String list parameter value", action="append",
                        metavar="VAL")


    

    parser.add_argument("--range", dest="paramSpecs", nargs='+', type=int,
                        help="Integer list created by range()", action=AppendRange,
                        metavar="VAL")
    parser.add_argument("--arange", dest="paramSpecs", nargs='+', type=float,
                        help="Float list created by numpy.arange()", action=AppendARange,
                        metavar="VAL")
    parser.add_argument("--linspace", dest="paramSpecs", nargs='+', type=float,
                        help="Float list created by numpy.linspace()", action=AppendLinspace,
                        metavar="VAL")
    parser.add_argument("--logspace", dest="paramSpecs", nargs='+', type=float,
                        help="Float list created by numpy.logspace()", action=AppendLogspace,
                        metavar="VAL")
    

    # The basic premise here is that we want to run a tracking algorithm
    # on a MultiSim (or a single simulation) multiple times.  Each tracking
    # run would have slightly different parameters.
    #
    # The way this is done is by creating a tracking parameter configuration file
    # that would contain an entry for each different tracking configuration.
    # Each configuration would get a unique name which is appended to the
    # end of the tracking results file.
    #
    # Then, when the tracking analysis or display is performed, one can direct them
    # to pick out only certain trackers of interest.
    #
    # So, this program will generate a tracking parameter file for use elsewhere.



    args = parser.parse_args()

    # Quickly fix any scalars to be a one-element list
    # Scalars are defined to be any non-sequencable item.
    for index, val in enumerate(args.paramSpecs) :
        if isinstance(val, (type(None),int,float,str,bool,dict)) :
            args.paramSpecs[index] = [val]


    print "Output File:", args.paramFile, "  Tracker:", args.tracker

    trackConfs = {}

    # ------------------------------------------------------------
    # Ok, let me explain the magic of the next line.
    # Three parts: first, I create numpy arrays out of the
    #       lists given for each parameter.  These lists are made
    #       such that their ndim == # of parameters.
    #
    #       Second, these arrays are broadcasted against each other.
    #
    #       Third, I flatten each of these arrays.
    #
    # The upshot of all of this is that I can loop through a zipped
    # representation of the arrays and experience every possible combination
    # of parameter values.
    # ---------------------------------------------------------
    paramSpecs = map(np.ravel, np.broadcast_arrays(*np.ix_(*args.paramSpecs)))

    for vals in zip(*paramSpecs) :
        trackrun = '_'.join("%s_%s" % (name, val) for name, val in zip(args.parameters, vals) if name not in args.silentParams)
        aConf = {'algorithm': args.tracker}
        aConf.update(zip(args.parameters, vals))
        trackConfs[args.tracker + '_' + trackrun] = aConf


    config = ConfigObj(trackConfs, interpolation=False)
    config.filename = args.paramFile
    config.write()


        # TODO: still need to modify the destination of the result files
#        MultiTrack(multiSimParams, trackConfs.dict(), path=args.directory)


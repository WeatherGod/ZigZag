#!/usr/bin/env python




if __name__ == "__main__" :
    import argparse         # Command-line parsing
    import os				# for os.sep.join()
    import glob				# for globbing
    import matplotlib.pyplot as pyplot
    import ParamUtils               # for ReadSimulationParams()
    from TrackPlot import *			# for plotting tracks
    from TrackFileUtils import *	# for reading track files
    from TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
    from ShowTracks import ShowTracks

    parser = argparse.ArgumentParser(description="Produce an animation of the tracks")
    parser.add_argument("trackFiles", nargs='*',
                        help="Use TRACKFILE for track data",
                        metavar="TRACKFILE")
    parser.add_argument("-t", "--truth", dest="truthTrackFile",
                      help="Use TRUTHFILE for true track data",
                      metavar="TRUTHFILE", default=None)
    parser.add_argument("-d", "--dir", dest="directory",
              help="Base directory to work from when using --simName",
              metavar="DIRNAME", default=".")
    parser.add_argument("-s", "--simName", dest="simName",
              help="Use data from the simulation SIMNAME",
              metavar="SIMNAME", default=None)

    args = parser.parse_args()

    # FIXME: Currently, the code allows for trackFiles to be listed as well
    #        as providing a simulation (which trackfiles are automatically grabbed).
    #        Both situations can not be handled right now, though.
    trackFiles = []
    trackTitles = []

    if args.simName is not None :
        simParams = ParamUtils.ReadSimulationParams(args.directory + os.sep + args.simName + os.sep + "simParams.conf")
        trackFiles = [args.directory + os.sep + simParams['result_file'] + '_' + aTracker
                        for aTracker in simParams['trackers']]
        trackTitles = simParams['trackers']

        if args.truthTrackFile is None :
            args.truthTrackFile = args.directory + os.sep + simParams['noisyTrackFile']

    trackFiles += args.trackFiles
    trackTitles += args.trackFiles


    if len(trackFiles) == 0 : print "WARNING: No trackFiles given or found!"

    trackerData = [FilterMHTTracks(*ReadTracks(trackFile)) for trackFile in trackFiles]


    # TODO: Dependent on the assumption that I am doing a comparison between 2 trackers
    theFig = pyplot.figure(figsize = (11, 5))

    if args.truthTrackFile is not None :
        truthData = FilterMHTTracks(*ReadTracks(args.truthTrackFile))
    else :
        truthData = None

    stackedTracks, stackedData, tLims = ShowTracks(trackerData, theFig, trackTitles, truthData=truthData,
                                                   animated=True)

    l = AnimateTracks(theFig, stackedTracks, stackedData, max(tLims) - min(tLims) + 1, interval=250)

    pyplot.show()

#!/usr/bin/env python

from ZigZag.TrackPlot import *			# for plotting tracks
from ZigZag.TrackFileUtils import *		# for reading track files
from ZigZag.TrackUtils import *		# for CreateSegments(), FilterMHTTracks(), DomainFromTracks()
import ZigZag.ParamUtils as ZigZag          # for ReadSimulationParams()


def main(args) :
    import os.path			# for os.path
    import glob				# for globbing
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid
    
    inputDataFiles = []
    titles = []

    if args.simName is not None :
        dirName = os.path.join(args.directory, args.simName)
        simParams = ParamUtils.ReadSimulationParams(os.path.join(dirName, "simParams.conf"))
        inputDataFiles.append(os.path.join(dirName, simParams['inputDataFile']))
        titles.append(args.simName)

    # Add on any files specified at the command-line
    inputDataFiles += args.inputDataFiles
    titles += args.inputDataFiles


    if len(inputDataFiles) == 0 : print "WARNING: No inputDataFiles given or found!"

    if args.layout is None :
        args.layout = (1, len(inputDataFiles))

    if args.figsize is None :
        args.figsize = plt.figaspect(float(args.layout[0]) / args.layout[1])

    cornerVolumes = [ReadCorners(inFileName, os.path.dirname(inFileName))['volume_data']
                     for inFileName in inputDataFiles]

    theFig = plt.figure(figsize=args.figsize)
    grid = AxesGrid(theFig, 111, nrows_ncols=args.layout,
                            share_all=True, axes_pad=0.32)

    # A list to hold the CircleCollection arrays, it will have length 
    # of max(tLims) - min(tLims) + 1
    allCorners = None

    if args.trackFile is not None :
        (tracks, falarms) = FilterMHTTracks(*ReadTracks(args.trackFile))
        (xLims, yLims, frameLims) = DomainFromTracks(tracks + falarms)
    else :
        volumes = []
        for aVol in cornerVolumes :
            volumes.extend(aVol)
        (xLims, yLims, frameLims) = DomainFromVolumes(volumes)

    theAnim = CornerAnimation(theFig, frameLims[1] - frameLims[0] + 1,
                              interval=250, blit=True)

    for (index, volData) in enumerate(cornerVolumes) :
        curAxis = grid[index]
        corners = PlotCorners(volData, frameLims, axis=curAxis)


        #curAxis.set_xlim(xLims)
        #curAxis.set_ylim(yLims)
        #curAxis.set_aspect("equal", 'datalim')
        #curAxis.set_aspect("equal")
        curAxis.set_title(titles[index])
        curAxis.set_xlabel("X")
        curAxis.set_ylabel("Y")

        theAnim.AddCornerVolume(corners)

    #theAnim.save("test.mp4")

    plt.show()



if __name__ == '__main__' :
    import argparse                         # Command-line parsing

    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Produce an animation of the centroids")
    AddCommandParser('ShowCorners', parser)
    """
    parser.add_argument("inputDataFiles", nargs='*',
                        help="Use INDATAFILE for finding corner data files",
                        metavar="INDATAFILE")

    parser.add_argument("-t", "--track", dest="trackFile",
                      help="Use TRACKFILE for determining domain limits.",
                      metavar="TRACKFILE", default=None)
    parser.add_argument("-l", "--layout", dest="layout", type=int,
                        nargs=2, help="Layout of the subplots (rows x columns). All plots on one row by default.",
                        metavar="NUM", default=None)
    parser.add_argument("-f", "--figsize", dest="figsize", type=float,
                        nargs=2, help="Size of the figure in inches (width x height). Default: %(default)s",
                        metavar="SIZE", default=(11.0, 5.0))
    parser.add_argument("-d", "--dir", dest="directory",
              help="Base directory to work from when using --simName",
              metavar="DIRNAME", default=".")
    parser.add_argument("-s", "--simName", dest="simName",
              help="Use data from the simulation SIMNAME.",
              metavar="SIMNAME", default=None)
    """
    args = parser.parse_args()

    main(args)


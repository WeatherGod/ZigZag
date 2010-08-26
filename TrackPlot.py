#------------------------
# for the animation code
#import gtk, gobject

#import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib.animation import FuncAnimation
#------------------------

import numpy
import matplotlib.pyplot as pyplot

#################################
#		Segment Plotting        #
#################################
def PlotSegment(lineSegs, tLims, axis=None, **kwargs) :
    if (axis is None) :
       axis = pyplot.gca()

    tLower = min(tLims)
    tUpper = max(tLims)

    lines = []
    for aSeg in lineSegs :
        mask = numpy.logical_and(tUpper >= aSeg['frameNums'],
                                 tLower <= aSeg['frameNums'])
	lines.append(axis.plot(aSeg['xLocs'][mask], aSeg['yLocs'][mask],
			       **kwargs)[0])

    return lines

def PlotSegments(truthTable, tLims,
	         axis=None, width=4.0, **kwargs) :
    if axis is None :
        axis = pyplot.gca()

    tableSegs = {}

    # Correct Stuff
    tableSegs['assocs_Correct'] = PlotSegment(truthTable['assocs_Correct'], tLims, axis,
                 			      linewidth=width, color= 'green', 
					      marker=' ', 
					      zorder=1, **kwargs)
    tableSegs['falarms_Correct'] = PlotSegment(truthTable['falarms_Correct'], tLims, axis,
             				       color='lightgreen', linestyle=' ', 
					       marker='.', markersize=2*width,
					       zorder=1, **kwargs)

    # Wrong Stuff
    tableSegs['falarms_Wrong'] = PlotSegment(truthTable['falarms_Wrong'], tLims, axis,
                 			     linewidth=width, color='gray', linestyle='-.',
					     dash_capstyle = 'round', 
					     marker=' ', #markersize = 2*width,
					     zorder=2, **kwargs)
    tableSegs['assocs_Wrong'] = PlotSegment(truthTable['assocs_Wrong'], tLims, axis,
    					    linewidth=width, color='red', 
					    marker=' ', 
					    zorder=2, **kwargs)



    return tableSegs

def Animate_Segments(truthTable, tLims, axis=None, figure=None, event_source=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    tableLines = PlotSegments(truthTable, tLims, axis=axis, animated=True) 

    theLines = []
    theSegs = []

    for keyname in tableLines :
        theLines += tableLines[keyname]
        theSegs += truthTable[keyname]

    return AnimateLines(theLines, theSegs, min(tLims), max(tLims), axis=axis, figure=figure, event_source=None, **kwargs)

#############################################
#           Corner Plotting                 #
#############################################
def PlotCorners(volData, tLims, axis=None, **kwargs) :
    if axis is None :
        axis = pyplot.gca()

    corners = []
    for aVol in volData :
        if aVol['volTime'] >= min(tLims) and aVol['volTime'] <= max(tLims) :
            corners.append(axis.scatter(aVol['stormCells']['xLocs'],
                                        aVol['stormCells']['yLocs'], s=1, **kwargs))

    return corners

def Animate_Corners(volData, tLims, axis=None, figure=None,
                    speed=1.0, loop_hold=2.0, event_source=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    corners = PlotCorners(volData, tLims, axis=axis, animated=True)

    startFrame = min(tLims)
    endFrame = max(tLims)

    def update_corners(idx, corners) :
        for index, scatterCol in enumerate(corners) :
            scatterCol.set_visible(index == idx)
            
        return corners

    return FuncAnimation(figure, update_corners, endFrame - startFrame + 1,
                         fargs=(corners,), event_source=event_source,
                         interval=500, blit=True)

#############################################
#           Animation Code                  #
#############################################
def AnimateLines(lines, lineData, startFrame, endFrame, 
                 figure=None, axis=None,
                 speed=1.0, loop_hold=2.0, tail=None, event_source=None) :

    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    if tail is None :
        tail = endFrame - startFrame

    def update_lines(idx, lineData, lines, firstFrame, lastFrame, tail) :
        theHead = min(max(idx, firstFrame), lastFrame)
        startTail = max(theHead - tail, firstFrame)
            
        for (index, (line, aSeg)) in enumerate(zip(lines, lineData)) :
            mask = numpy.logical_and(aSeg['frameNums'] <= theHead,
                                     aSeg['frameNums'] >= startTail)
		
            line.set_xdata(aSeg['xLocs'][mask])
            line.set_ydata(aSeg['yLocs'][mask])
        return lines

    return FuncAnimation(figure, update_lines, endFrame - startFrame + 1,
                         fargs=(lineData, lines, startFrame, endFrame, tail),
                         interval=500, blit=True, event_source=event_source)


###################################################
#		Track Plotting                            #
###################################################
def PlotTrack(tracks, tLims, axis=None, **kwargs) :
    if axis is None :
        axis = pyplot.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    lines = []
    for aTrack in tracks :
        mask = numpy.logical_and(aTrack['frameNums'] <= endFrame,
                                 aTrack['frameNums'] >= startFrame)
        lines.append(axis.plot(aTrack['xLocs'][mask], aTrack['yLocs'][mask],
			       **kwargs)[0])

    return lines



def PlotTracks(true_tracks, model_tracks, tLims, startFrame=None, endFrame=None,
	       axis=None, animated=False) :
    if axis is None :
        axis = pyplot.gca()

    if startFrame is None : startFrame = min(tLims)
    if endFrame is None : endFrame = max(tLims)

    trueLines = PlotTrack(true_tracks, tLims,
			  marker='.', markersize=9.0,
			  color='grey', linewidth=2.5, linestyle=':', 
			  animated=False, zorder=1, axis=axis)
    modelLines = PlotTrack(model_tracks, (startFrame, endFrame), 
			   marker='.', markersize=8.0, 
			   color='r', linewidth=2.5, alpha=0.55, 
			   zorder=2, animated=animated, axis=axis)
    return {'trueLines': trueLines, 'modelLines': modelLines}

def PlotPlainTracks(tracks, falarms, tLims, startFrame=None, endFrame=None, axis=None, animated=False) :
    if axis is None :
        axis = pyplot.gca()

    if startFrame is None : startFrame = min(tLims)
    if endFrame is None : endFrame = max(tLims)

    trackLines = PlotTrack(tracks, tLims, axis=axis, marker='.', markersize=6.0,
                           color='k', linewidth=1.5, animated=animated)
    falarmLines = PlotTrack(falarms, tLims, axis=axis, marker='.', markersize=6.0,
                            linestyle=' ', color='r', animated=animated)

    return {'trackLines': trackLines, 'falarmLines': falarmLines}



def Animate_Tracks(true_tracks, model_tracks, tLims, 
                   axis=None, figure=None, event_source=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, tLims, 
                          startFrame, endFrame, axis=axis, animated=True)

    return AnimateLines(theLines['trueLines'] + theLines['modelLines'],
                        true_tracks + model_tracks, startFrame, endFrame,
                        axis=axis, figure=figure, event_source=event_source, **kwargs)


def Animate_PlainTracks(tracks, falarms, tLims, figure=None,
                        axis=None, event_source=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    # Create the initial lines
    theLines = PlotPlainTracks(tracks, falarms, tLims,
                               startFrame, endFrame, axis=axis, animated=True)

    return AnimateLines(theLines['trackLines'] + theLines['falarmLines'],
                        tracks + falarms, startFrame, endFrame, axis=axis, figure=figure, event_source=event_source, **kwargs)



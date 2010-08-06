#------------------------
# for the animation code
import gtk, gobject

import matplotlib
matplotlib.use('GTKAgg')
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

def Animate_Segments(truthTable, tLims, axis=None, figure=None, **kwargs) :
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

    AnimateLines(theLines, theSegs, min(tLims), max(tLims), axis=axis, figure=figure, **kwargs)

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
                    speed=1.0, loop_hold=2.0, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = pyplot.gca()

    corners = PlotCorners(volData, tLims, axis=axis, animated=True)

    startFrame = min(tLims)
    endFrame = max(tLims)

    canvas = figure.canvas
    canvas.draw()

    def update_corners(*args) :
        if update_corners.background is None :
            update_corners.background = canvas.copy_from_bbox(axis.bbox)

        if (int(update_corners.cnt) > update_corners.currFrame) :
            update_corners.currFrame = int(update_corners.cnt)
            canvas.restore_region(update_corners.background)

            for index, scatterCol in enumerate(corners) :
                scatterCol.set_visible(index == update_corners.currFrame)
                axis.draw_artist(scatterCol)

            canvas.blit(axis.bbox)

        if update_corners.cnt >= (endFrame + (loop_hold - speed)):
            update_corners.cnt = startFrame
            update_corners.currFrame = startFrame - 1.

        update_corners.cnt += speed
        return(True)

    update_corners.cnt = endFrame
    update_corners.currFrame = startFrame - 1.
    update_corners.background = None


    def start_anim(event):
        gobject.idle_add(update_corners)
        canvas.mpl_disconnect(start_anim.cid)

    start_anim.cid = canvas.mpl_connect('draw_event', start_anim)

#############################################
#           Animation Code                  #
#############################################
def AnimateLines(lines, lineData, startFrame, endFrame, 
                 figure=None, axis=None,
                 speed=1.0, loop_hold=2.0, tail=None) :

    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    if tail is None :
        tail = endFrame - startFrame

    canvas = figure.canvas
    canvas.draw()

    def update_line(*args) :
        if update_line.background is None:
            update_line.background = canvas.copy_from_bbox(axis.bbox)

        
        if (int(update_line.cnt) > update_line.currFrame) : 
            update_line.currFrame = int(update_line.cnt)
            canvas.restore_region(update_line.background)

            theHead = min(max(update_line.currFrame, startFrame), endFrame)
            startTail = max(theHead - tail, startFrame)
            

            for (index, (line, aSeg)) in enumerate(zip(lines, lineData)) :
                mask = numpy.logical_and(aSeg['frameNums'] <= theHead,
                                         aSeg['frameNums'] >= startTail)
		
                line.set_xdata(aSeg['xLocs'][mask])
                line.set_ydata(aSeg['yLocs'][mask])

                axis.draw_artist(line)
		
        canvas.blit(axis.bbox)

        if update_line.cnt >= (endFrame + (loop_hold - speed)):
            update_line.cnt = startFrame
            update_line.currFrame = startFrame - 1.

        update_line.cnt += speed
        return(True)

    update_line.cnt = endFrame
    update_line.currFrame = startFrame - 1.
    update_line.background = None
    
 
    def start_anim(event):
        gobject.idle_add(update_line)
        canvas.mpl_disconnect(start_anim.cid)

    start_anim.cid = canvas.mpl_connect('draw_event', start_anim)


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
                   axis=None, figure=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, tLims, 
                          startFrame, endFrame, axis=axis, animated=True)

    AnimateLines(theLines['trueLines'] + theLines['modelLines'],
                 true_tracks + model_tracks, startFrame, endFrame,
                 axis=axis, figure=figure, **kwargs)


def Animate_PlainTracks(tracks, falarms, tLims, figure=None,
                        axis=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    # Create the initial lines
    theLines = PlotPlainTracks(tracks, falarms, tLims,
                               startFrame, endFrame, axis=axis, animated=True)

    AnimateLines(theLines['trackLines'] + theLines['falarmLines'],
                 tracks + falarms, startFrame, endFrame, axis=axis, figure=figure, **kwargs)



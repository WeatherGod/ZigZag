import gtk, gobject

import matplotlib
matplotlib.use('GTKAgg')

#import pylab
import numpy
import matplotlib.pyplot as pyplot

#################################################
#		Segment Plotting		#
#################################################

def PlotSegment(lineSegs, xLims, yLims, tLims, axis=None, **kwargs) :
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

#    axis.set_xlim(xLims)
#    axis.set_ylim(yLims)

    return lines

def PlotSegments(truthTable, xLims, yLims, tLims,
	         axis=None, width=4.0, **kwargs) :
    if axis is None :
        axis = pyplot.gca()

    tableSegs = {}

    # Correct Stuff
    tableSegs['assocs_Correct'] = PlotSegment(truthTable['assocs_Correct'], xLims, yLims, tLims, axis,
                 			      linewidth=width, color= 'green', 
					      marker=' ', 
					      zorder=1, **kwargs)
    tableSegs['falarms_Correct'] = PlotSegment(truthTable['falarms_Correct'], xLims, yLims, tLims, axis,
             				       color='lightgreen', linestyle=' ', 
					       marker='.', markersize=2*width,
					       zorder=1, **kwargs)

    # Wrong Stuff
    tableSegs['falarms_Wrong'] = PlotSegment(truthTable['falarms_Wrong'], xLims, yLims, tLims, axis,
                 			     linewidth=width, color='gray', linestyle='-.',
					     dash_capstyle = 'round', 
					     marker=' ', #markersize = 2*width,
					     zorder=2, **kwargs)
    tableSegs['assocs_Wrong'] = PlotSegment(truthTable['assocs_Wrong'], xLims, yLims, tLims, axis,
    					    linewidth=width, color='red', 
					    marker=' ', 
					    zorder=2, **kwargs)



    return tableSegs

def Animate_Segments(truthTable, xLims, yLims, tLims, axis=None, **kwargs) :
    if axis is None :
	axis = pyplot.gca()

    tableLines = PlotSegments(truthTable, xLims, yLims, tLims, axis=axis, animated=True) 

    theLines = []
    theSegs = []

    for keyname in tableLines :
        theLines += tableLines[keyname]
        theSegs += truthTable[keyname]

    AnimateLines(theLines, theSegs, min(tLims), max(tLims), axis=axis, **kwargs)




def AnimateLines(lines, lineData, startFrame, endFrame, 
		 speed=1.0, loop_hold=2.0, figure=None, axis=None) :
    if figure is None :
	figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    canvas = figure.canvas
    canvas.draw()

    def update_line(*args) :
        if update_line.background is None:
            update_line.background = canvas.copy_from_bbox(axis.bbox)

        
	if (int(update_line.cnt) > update_line.currFrame) : 
	    update_line.currFrame = int(update_line.cnt)

            canvas.restore_region(update_line.background)

	    for (index, (line, aSeg)) in enumerate(zip(lines, lineData)) :
                mask = numpy.logical_and(aSeg['frameNums'] <= update_line.currFrame,
                                         aSeg['frameNums'] >= startFrame)
		
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
#		Track Plotting			  #
###################################################

def PlotTrack(tracks, xLims, yLims, tLims, axis=None, **kwargs) :
    if axis is None :
        axis = pyplot.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    lines = []
    for aTrack in tracks :
        mask = numpy.logical_and(aTrack['frameNums'] <= endFrame,
                                 aTrack['frameNums'] >= startFrame)
        lines.append(axis.plot(aTrack['xLocs'][mask], aTrack['yLocs'][mask]
			       **kwargs)[0])
    #axis.set_xlim(xLims)
    #axis.set_ylim(yLims)

    return lines



def PlotTracks(true_tracks, model_tracks, xLims, yLims, tLims, startFrame=None, endFrame=None,
	       axis=None, animated=False) :
    if axis is None :
        axis = pyplot.gca()

    if startFrame is None : startFrame = min(tLims)
    if endFrame is None : endFrame = max(tLims)

    trueLines = PlotTrack(true_tracks, xLims, yLims, tLims,
			  marker='.', markersize=9.0,
			  color='grey', linewidth=2.5, linestyle=':', 
			  animated=False, zorder=1, axis=axis)
    modelLines = PlotTrack(model_tracks, xLims, yLims, (startFrame, endFrame), 
			   marker='.', markersize=8.0, 
			   color='r', linewidth=2.5, alpha=0.55, 
			   zorder=2, animated=animated, axis=axis)
    return {'trueLines': trueLines, 'modelLines': modelLines}



def Animate_Tracks(true_tracks, model_tracks, xLims, yLims, tLims, 
		   speed=1.0, loop_hold=2.0, figure=None, axis=None) :
    if (axis is None) :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    axis.hold(True)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, xLims, yLims, tLims, 
			  startFrame, endFrame, axis=axis, animated=True)

    AnimateLines(theLines['modelLines'], model_tracks, startFrame, endFrame, axis=axis, figure=figure)
    


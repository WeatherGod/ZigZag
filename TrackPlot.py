import gtk, gobject

import matplotlib
matplotlib.use('GTKAgg')

import pylab

#################################################
#		Segment Plotting		#
#################################################

def PlotSegment(lineSegs, xLims, yLims, tLims, axis=None, **kwargs) :
    if (axis is None) :
       axis = pylab.gca()



    lines = []
    for (segXLocs, segYLocs, segFrameNums) in zip(lineSegs['xLocs'], lineSegs['yLocs'], lineSegs['frameNums']) :
	#if (min(segFrameNums) >= min(tLims) and max(segFrameNums) <= max(tLims)) :
	lines.append(axis.plot([segXLoc for (segXLoc, frameNum) in zip(segXLocs, segFrameNums) if min(tLims) <= frameNum <= max(tLims)],
			       [segYLoc for (segYLoc, frameNum) in zip(segYLocs, segFrameNums) if min(tLims) <= frameNum <= max(tLims)],
			       **kwargs)[0])
	#else :
	    # This guarantees that the lines list will be the same length
	    # as the lineSegs list.
	    #lines.append(axis.plot([], [])[0])

    axis.set_xlim(xLims)
    axis.set_ylim(yLims)

    return lines

def PlotSegments(truthTable, xLims, yLims, tLims,
	         axis = None, animated=False, width = 4.0) :
    if axis is None :
        axis = pylab.gca()

    tableSegs = {}

    # Correct Stuff
    tableSegs['assocs_Correct'] = PlotSegment(truthTable['assocs_Correct'], xLims, yLims, tLims, axis,
                 			      linewidth=width, color= 'green', 
					      marker=' ', 
					      animated=animated, zorder=1)
    tableSegs['falarms_Correct'] = PlotSegment(truthTable['falarms_Correct'], xLims, yLims, tLims, axis,
             				       color='lightgreen', linestyle=' ', 
					       marker='.', markersize=2*width,
					       animated=animated, zorder=1)

    # Wrong Stuff
    tableSegs['falarms_Wrong'] = PlotSegment(truthTable['falarms_Wrong'], xLims, yLims, tLims, axis,
                 			     linewidth=width, color='gray', linestyle='-.',
					     dash_capstyle = 'round', 
					     marker=' ', #markersize = 2*width,
					     animated=animated, zorder=2)
    tableSegs['assocs_Wrong'] = PlotSegment(truthTable['assocs_Wrong'], xLims, yLims, tLims, axis,
    					    linewidth=width, color='red', 
					    marker=' ', 
					    animated=animated, zorder=2)



    return tableSegs

def Animate_Segments(truthTable, xLims, yLims, tLims, axis = None, **kwargs) :
    if axis is None :
	axis = pylab.gca()

    tableLines = PlotSegments(truthTable, xLims, yLims, tLims, axis = axis, animated = True) 

    theLines = []
    theSegs = []

    for keyname in tableLines :
        theLines += tableLines[keyname]
	for (frameNums, xLocs, yLocs) in zip(truthTable[keyname]['frameNums'],
					     truthTable[keyname]['xLocs'],
					     truthTable[keyname]['yLocs']) :
	    theSegs.append({'frameNums': frameNums, 'xLocs': xLocs, 'yLocs': yLocs})

    AnimateLines(theLines, theSegs, min(tLims), max(tLims), axis = axis, **kwargs)




def AnimateLines(lines, lineData, startFrame, endFrame, 
		 speed = 1.0, hold_loop = 2.0, figure = None, axis = None) :
    if figure is None :
	figure = pylab.gcf()

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

	    for (index, (line, aLineData)) in enumerate(zip(lines, lineData)) :
		newLine = [(xLoc, yLoc) for xLoc, yLoc, frameNum in zip(aLineData['xLocs'],
									aLineData['yLocs'],
									aLineData['frameNums'])
								  if frameNum <= update_line.currFrame
								      and frameNum >= startFrame]
		if len(newLine) == 0 :
		    xLocs = []
		    yLocs = []
		else :
		    xLocs, yLocs = zip(*newLine)

		line.set_xdata(xLocs)
		line.set_ydata(yLocs)

                axis.draw_artist(line)
		
        canvas.blit(axis.bbox)

        if update_line.cnt >= (endFrame + (hold_loop - speed)):
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
    if (axis is None) :
        axis = pylab.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    lines = []
    for aTrack in tracks :
        lines.append(axis.plot([xLoc for (xLoc, frameNum) in zip(aTrack['xLocs'], aTrack['frameNums']) if frameNum <= endFrame 
														and frameNum >= startFrame],
			       [yLoc for (yLoc, frameNum) in zip(aTrack['yLocs'], aTrack['frameNums']) if frameNum <= endFrame 
														and frameNum >= startFrame],
			       **kwargs)[0])
    axis.set_xlim(xLims)
    axis.set_ylim(yLims)

    return lines



def PlotTracks(true_tracks, model_tracks, xLims, yLims, tLims, startFrame=None, endFrame=None,
	       axis = None, animated=False) :
    if axis is None :
        axis = pylab.gca()

    if startFrame is None : startFrame = min(tLims)
    if endFrame is None : endFrame = max(tLims)

    trueLines = PlotTrack(true_tracks, xLims, yLims, tLims,
			  marker='.', markersize=9.0,
			  color='grey', linewidth=2.5, linestyle=':', 
			  animated=False, zorder=1, axis = axis)
    modelLines = PlotTrack(model_tracks, xLims, yLims, (startFrame, endFrame), 
			   marker='.', markersize=8.0, 
			   color='r', linewidth=2.5, alpha=0.55, 
			   zorder=2, animated=animated, axis = axis)
    return({'trueLines': trueLines, 'modelLines': modelLines})



def Animate_Tracks(true_tracks, model_tracks, xLims, yLims, tLims, 
		   speed = 1.0, hold_loop = 2.0, figure = None, axis = None) :
    if (axis is None) :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    axis.hold(True)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, xLims, yLims, tLims, 
			  startFrame, endFrame, axis = axis, animated = True)

    AnimateLines(theLines['modelLines'], model_tracks, startFrame, endFrame, axis = axis, figure = figure)
    


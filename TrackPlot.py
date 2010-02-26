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
	         axis = None, animated=False) :
    if axis is None :
        axis = pylab.gca()

    tableSegs = {}

    # Correct Stuff
    tableSegs['assocs_Correct'] = PlotSegment(truthTable['assocs_Correct'], xLims, yLims, tLims, axis,
                 			      linewidth=1.5, color= 'green', 
					      marker='.', markersize=6.0, animated=animated, zorder=1)
    tableSegs['falarms_Correct'] = PlotSegment(truthTable['falarms_Correct'], xLims, yLims, tLims, axis,
             				       color='green', linestyle=' ', 
					       marker='.', markersize=6.0, animated=animated, zorder=1)

    # Wrong Stuff
    tableSegs['falarms_Wrong'] = PlotSegment(truthTable['falarms_Wrong'], xLims, yLims, tLims, axis,
                 			     linewidth=3.0, color='gray', linestyle=':',
					     marker='.', markersize=9.0, animated=animated, zorder=2)
    tableSegs['assocs_Wrong'] = PlotSegment(truthTable['assocs_Wrong'], xLims, yLims, tLims, axis,
    					    linewidth=3.0, color='red', 
					    marker='.', markersize=9.0, animated=animated, zorder=2)



    return tableSegs

def Animate_Segments(truthTable, xLims, yLims, tLims,
		     speed = 1.0, hold_loop = 2.0, figure = None, axis = None) :
    if figure is None :
	figure = pylab.gcf()

    if (axis is None) :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    canvas = figure.canvas


    # Placed before the initial creation of line segments in
    # order to avoid having it mess up the axes...
    #emptyLine = axis.plot([], [])[0]

    # create the initial lines
    print truthTable.keys()
    tableLines = PlotSegments(truthTable, xLims, yLims, tLims, axis = axis, animated=True)
    canvas.draw()

    theLines = []
    theSegs_frames = []
    theSegs_xLocs = []
    theSegs_yLocs = []

    for keyname in tableLines :
        theLines += tableLines[keyname]
	theSegs_frames += truthTable[keyname]['frameNums']
	theSegs_xLocs += truthTable[keyname]['xLocs']
	theSegs_yLocs += truthTable[keyname]['yLocs']

    def update_line(*args) :
        if update_line.background is None:
            update_line.background = canvas.copy_from_bbox(axis.bbox)

        
	if (int(update_line.cnt) > update_line.currFrame) :
	    update_line.currFrame = int(update_line.cnt)

            canvas.restore_region(update_line.background)

	    for (line, segFrameNums, segXLocs, segYLocs) in zip(theLines, theSegs_frames, 
								theSegs_xLocs, theSegs_yLocs) :
                line.set_xdata([xLoc for (xLoc, frameNum) in zip(segXLocs, segFrameNums) if frameNum <= update_line.currFrame 
											    and frameNum >= startFrame])
                line.set_ydata([yLoc for (yLoc, frameNum) in zip(segYLocs, segFrameNums) if frameNum <= update_line.currFrame 
											    and frameNum >= startFrame])
                axis.draw_artist(line)
		
	    """
            for (line, frameNums) in zip(theLines, theSegs['frameNums']) :
	        if min(frameNums) >= startFrame and max(frameNums) <= update_line.cnt :
		    axis.draw_artist(line)
	        else :
		    # This is done to help even out the time it takes to
		    # render each frame, regardless of how many components
		    # are needed to show a particular frame.
		    axis.draw_artist(emptyLine)
#		     line.set_xdata(aSeg['xLocs'])
#		     line.set_ydata(aSeg['yLocs'])
	    """
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

    lines = []
    for aTrack in tracks :
        lines.append(axis.plot([xLoc for (xLoc, frameNum) in zip(aTrack['xLocs'], aTrack['frameNums']) if frameNum >= min(tLims) and frameNum <= max(tLims)],
			       [yLoc for (yLoc, frameNum) in zip(aTrack['yLocs'], aTrack['frameNums']) if frameNum >= min(tLims) and frameNum <= max(tLims)],
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
			  color='gray', linewidth=2.5, linestyle=':', 
			  animated=animated, zorder=1, axis = axis)
    modelLines = PlotTrack(model_tracks, xLims, yLims, (startFrame, endFrame), 
			   marker='.', markersize=8.0, 
			   color='r', linewidth=2.5, alpha=0.35, 
			   zorder=2, animated=animated, axis = axis)
    return({'trueLines': trueLines, 'modelLines': modelLines})



def Animate_Tracks(true_tracks, model_tracks, xLims, yLims, tLims, 
		   speed = 1.0, hold_loop = 2.0, figure = None, axis = None) :
    if figure is None :
	figure = pylab.gcf()

    if (axis is None) :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    canvas = figure.canvas

    # create the initial lines
    
    theLines = PlotTracks(true_tracks, model_tracks, xLims, yLims, tLims, 
			  startFrame, startFrame, axis = axis, animated = True)
    canvas.draw()
    

    def update_line(*args) :
        if update_line.background is None:
            update_line.background = canvas.copy_from_bbox(axis.bbox)

	if (int(update_line.cnt) > update_line.currFrame) :
            update_line.currFrame = int(update_line.cnt)

	    canvas.restore_region(update_line.background)

            for (line, frameNums, aTrackXLocs, aTracksYLocs) in zip(theLines['modelLines'], *model_tracks) :
                line.set_xdata([xLoc for (xLoc, frameNum) in zip(aTrack['xLocs'], aTrack['frameNums']) if frameNum <= update_line.cnt and frameNum >= startFrame])
                line.set_ydata([yLoc for (yLoc, frameNum) in zip(aTrack['yLocs'], aTrack['frameNums']) if frameNum <= update_line.cnt and frameNum >= startFrame])
                axis.draw_artist(line)

        canvas.blit(axis.bbox)

        if update_line.cnt >= (endFrame + (hold_loop - speed)):
            update_line.cnt = startFrame
	    update_line.currFrame = startFrame - 1.0

        update_line.cnt += speed
        return(True)

    update_line.cnt = endFrame
    update_line.currFrame = startFrame - 1.0
    update_line.background = None
    
 
    def start_anim(event):
        gobject.idle_add(update_line)
        canvas.mpl_disconnect(start_anim.cid)

    start_anim.cid = canvas.mpl_connect('draw_event', start_anim)



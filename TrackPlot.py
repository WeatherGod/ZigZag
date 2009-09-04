import gtk, gobject

import matplotlib
matplotlib.use('GTKAgg')

import pylab

def PlotSegments(lineSegs, xLims, yLims, tLims, axis=None, **kwargs) :
    if (axis is None) :
       axis = pylab.gca()

    lines = []
    for (segXLocs, segYLocs, segFrameNums) in zip(lineSegs['xLocs'], lineSegs['yLocs'], lineSegs['frameNums']) :
	if (min(segFrameNums) >= min(tLims) and max(segFrameNums) <= max(tLims)) :
	    lines.append(axis.plot(segXLocs, segYLocs, **kwargs)[0])

    axis.set_xlim(xLims)
    axis.set_ylim(yLims)

    return lines


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

    if startFrame is None : startFrame = min(tLims)
    if endFrame is None : endFrame = max(tLims)

    trueLines = PlotTrack(true_tracks, xLims, yLims, tLims,
			  marker='.', markersize=7.0, linestyle='solid', color='gray', linewidth=1.5, zorder=1, axis = axis)
    modelLines = PlotTrack(model_tracks, xLims, yLims, (startFrame, endFrame), 
			   marker='.', markersize=6.0, color='r', linewidth=1.5, alpha=0.5, zorder=2, animated=animated, axis = axis)
    return({'trueLines': trueLines, 'modelLines': modelLines})


def perform_animation(true_tracks, model_tracks, xLims, yLims, tLims, speed = 1.0, hold_loop = 2.0, axis = None) :
    if (axis is None) :
       axis = pylab.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    canvas = pylab.gcf().canvas

    # create the initial lines
    
    theLines = PlotTracks(true_tracks, model_tracks, xLims, yLims, tLims, 
			  startFrame, startFrame, axis = axis)
    canvas.draw()
    

    def update_line(*args) :
        if update_line.background is None:
           update_line.background = canvas.copy_from_bbox(axis.bbox)
        canvas.restore_region(update_line.background)
        for (line, aTrack) in zip(theLines['modelLines'], model_tracks) :
           line.set_xdata([xLoc for (xLoc, frameNum) in zip(aTrack['xLocs'], aTrack['frameNums']) if frameNum <= update_line.cnt and frameNum >= startFrame])
           line.set_ydata([yLoc for (yLoc, frameNum) in zip(aTrack['yLocs'], aTrack['frameNums']) if frameNum <= update_line.cnt and frameNum >= startFrame])
           axis.draw_artist(line)

        canvas.blit(axis.bbox)
        if update_line.cnt >= (endFrame + (hold_it - speed)):
           update_line.cnt = startFrame - speed

        update_line.cnt += speed
        return(True)

    update_line.cnt = endFrame
    update_line.background = None
    
 
    def start_anim(event):
        gobject.idle_add(update_line)
        canvas.mpl_disconnect(start_anim.cid)

    start_anim.cid = canvas.mpl_connect('draw_event', start_anim)



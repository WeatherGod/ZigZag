import gtk, gobject

import matplotlib
matplotlib.use('GTKAgg')

import pylab

def perform_animation(tracks, startFrame, endFrame) :
    fig = pylab.figure()
    ax = fig.add_subplot(111)
    canvas = fig.canvas

#    fig.subplots_adjust(left=0.3, bottom=0.3) # check for flipy bugs
    ax.grid() # to ensure proper background restore

    # create the initial lines
    ax.hold(True)
    lines = []
    for aTrack in tracks :
        lines.append(ax.plot([cell['xLoc'] for cell in aTrack['track'] if cell['type'] == 'M' and cell['frameNum'] >= startFrame and cell['frameNum'] <= endFrame],
                             [cell['yLoc'] for cell in aTrack['track'] if cell['type'] == 'M' and cell['frameNum'] >= startFrame and cell['frameNum'] <= endFrame], 
			     animated=True, linewidth=1.5, marker='x')[0])

    ax.hold(False)
    canvas.draw()

    def update_line(*args) :
        if update_line.background is None:
           update_line.background = canvas.copy_from_bbox(ax.bbox)
        canvas.restore_region(update_line.background)
        for (line, aTrack) in zip(lines, tracks) :
           line.set_xdata([cell['xLoc'] for cell in aTrack['track'] if cell['type'] == 'M' and cell['frameNum'] <= update_line.cnt and cell['frameNum'] >= startFrame])
           line.set_ydata([cell['yLoc'] for cell in aTrack['track'] if cell['type'] == 'M' and cell['frameNum'] <= update_line.cnt and cell['frameNum'] >= startFrame])
           ax.draw_artist(line)
        canvas.blit(ax.bbox)
        if update_line.cnt == endFrame :
           update_line.cnt = startFrame - 1

        update_line.cnt += 1
        return(True)

    update_line.cnt = endFrame
    update_line.background = None
    
 
    def start_anim(event):
        gobject.idle_add(update_line)
        canvas.mpl_disconnect(start_anim.cid)


    start_anim.cid = canvas.mpl_connect('draw_event', start_anim)
    pylab.show()


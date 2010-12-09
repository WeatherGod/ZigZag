#------------------------
# for the animation code
#import gtk, gobject

#import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib.animation import FuncAnimation
#------------------------

import numpy
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll

#################################
#		Segment Plotting        #
#################################
def PlotSegment(lineSegs, tLims, axis=None, **kwargs) :
    return PlotTrack(lineSegs, tLims, axis=axis, **kwargs)
    """
    if (axis is None) :
       axis = plt.gca()

    tLower = min(tLims)
    tUpper = max(tLims)

    lines = []
    for aSeg in lineSegs :
        mask = numpy.logical_and(tUpper >= aSeg['frameNums'],
                                 tLower <= aSeg['frameNums'])
	lines.append(axis.plot(aSeg['xLocs'][mask], aSeg['yLocs'][mask],
			       **kwargs)[0])

    return lines
    """

def PlotSegments(truthTable, tLims,
	         axis=None, width=4.0, **kwargs) :
    if axis is None :
        axis = plt.gca()

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
        figure = plt.gcf()

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
        axis = plt.gca()

    corners = []
    for aVol in volData :
        if aVol['volTime'] >= min(tLims) and aVol['volTime'] <= max(tLims) :
            newitem = mcoll.CircleCollection([1], offsets=zip(aVol['stormCells']['xLocs'],
                                                              aVol['stormCells']['yLocs']),
                                             transOffset=axis.transData, **kwargs)
            axis.add_collection(newitem)
        else :
            # an empty circle collection
            newitem = mcoll.CircleCollection([], offsets=zip([], []), transOffset=axis.transData)

        axis.add_collection(newitem)
        corners.append(newitem)

    return corners

class GeneralTrackAnim(FuncAnimation) :
    def __init__(self, figure, frameCnt, **kwargs) :
        self._allitems = []
        self._flatitems = []
        self._myframeCnt = frameCnt
        self._init_vis_state = True

        FuncAnimation.__init__(self, figure, self._update_items,
                                     frameCnt, fargs=(self._allitems,),
                                     **kwargs)

    def _update_items(self, idx, items) :
        raise NotImplementedError("Derived class must implement this")

    def _init_draw(self) :
        for anItem in self._flatitems :
            anItem.set_visible(self._init_vis_state)

class CornerAnimation(GeneralTrackAnim) :
    def __init__(self, figure, frameCnt, **kwargs) :
        GeneralTrackAnim.__init__(self, figure, frameCnt, **kwargs)
        self._init_vis_state = False

    def _update_items(self, idx, corners) :
        for index, scatterCol in enumerate(zip(*corners)) :
            for aCollection in scatterCol :
                aCollection.set_visible(index == idx)
            
        return self._flatitems

    def AddCornerVolume(self, corners) :
        if len(corners) > self._myframeCnt :
            self._myframeCnt = len(corners)
        self._allitems.append(corners)
        self._flatitems.extend(corners)


class TruthTableAnimation(GeneralTrackAnim) :
    def __init__(self, figure, frameCnt, **kwargs) :
        GeneralTrackAnim.__init__(self, figure, frameCnt, **kwargs)
        self._init_vis_state = True

    def _update_items(self, idx, vols) :
        #print "Another Update!", idx
        for index, lines in enumerate(vols) :
            isVis = (index <= idx)
            #print isVis
            for aLine in lines :
                aLine.set_visible(isVis)

        return self._flatitems

    def AddTruthTable(self, segVols) :
        if len(segVols) > len(self._allitems) :
            # extend the frames in _allitems by the difference in length
            self._allitems.extend([[]] * (len(segVols) - len(self._allitems)))
            self._myframeCnt = len(segVols)

        for aVol, newVol in zip(self._allitems, segVols) :
            aVol.extend(newVol)
            self._flatitems.extend(newVol)

#############################################
#           Animation Code                  #
#############################################
def AnimateLines(lines, lineData, startFrame, endFrame, 
                 figure=None, axis=None,
                 speed=1.0, loop_hold=2.0, tail=None, event_source=None) :

    if figure is None :
        figure = plt.gcf()

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
def PlotTrackVol(segs, frameLims, axis=None, **kwargs) :
    if axis is None :
        axis = plt.gca()

    frames = numpy.arange(min(frameLims), max(frameLims) + 1)

    volSegs = []
    for frameIndex in frames :
        currSegs = [plt.Line2D(aSeg['xLocs'], aSeg['yLocs'], **kwargs)
                    for aSeg in segs
                    if aSeg['frameNums'][0] == frameIndex]
        
        for aSeg in currSegs :
            axis.add_line(aSeg)
        volSegs.append(currSegs)

    return volSegs

def PlotTruthTable(truthTable, frameLims, axis=None, **kwargs) :
    if axis is None :
        axis = plt.gca()

    width = 2

    # Correct Stuff
    assocs_Correct = PlotTrackVol(truthTable['assocs_Correct'], frameLims, axis,
                                  linewidth=width, color= 'green',
                          marker=' ',
                          zorder=1, **kwargs)
    falarms_Correct = PlotTrackVol(truthTable['falarms_Correct'], frameLims, axis,
                                   color='lightgreen', linestyle=' ',
                           marker='.', markersize=2*width,
                           zorder=1, **kwargs)

    # Wrong Stuff
    falarms_Wrong = PlotTrackVol(truthTable['falarms_Wrong'], frameLims, axis,
                                 linewidth=width, color='gray', linestyle='-.',
                         dash_capstyle = 'round',
                         marker=' ', #markersize = 2*width,
                         zorder=2, **kwargs)
    assocs_Wrong = PlotTrackVol(truthTable['assocs_Wrong'], frameLims, axis,
                            linewidth=width, color='red',
                        marker=' ',
                        zorder=2, **kwargs)

    volColls = [C + F + M + N for C, F, M, N in zip(assocs_Correct, assocs_Wrong,
                                                    falarms_Wrong, falarms_Correct)]

    return volColls



def PlotTrack(tracks, tLims, axis=None, **kwargs) :
    if axis is None :
        axis = plt.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    lines = []
    for aTrack in tracks :
        mask = numpy.logical_and(aTrack['frameNums'] <= endFrame,
                                 aTrack['frameNums'] >= startFrame)
        newLine = plt.Line2D(aTrack['xLocs'][mask], aTrack['yLocs'][mask],
                             **kwargs)
        axis.add_line(newLine)
        lines.append(newLine)

    return lines



def PlotTracks(true_tracks, model_tracks, tLims, startFrame=None, endFrame=None,
	       axis=None, animated=False) :
    if axis is None :
        axis = plt.gca()

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
        axis = plt.gca()

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
        figure = plt.gcf()

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
        figure = plt.gcf()

    if axis is None :
        axis = figure.gca()

    startFrame = min(tLims)
    endFrame = max(tLims)

    # Create the initial lines
    theLines = PlotPlainTracks(tracks, falarms, tLims,
                               startFrame, endFrame, axis=axis, animated=False)

    return AnimateLines(theLines['trackLines'] + theLines['falarmLines'],
                        tracks + falarms, startFrame, endFrame, axis=axis, figure=figure, event_source=event_source, **kwargs)



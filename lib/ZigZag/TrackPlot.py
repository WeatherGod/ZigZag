#------------------------
# for the animation code
#import gtk, gobject

#import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib.animation import FuncAnimation
#------------------------

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.collections as mcoll

#################################
#		Segment Plotting        #
#################################
def PlotSegment(lineSegs, tLims, axis=None, **kwargs) :
    if (axis is None) :
       axis = plt.gca()

    tLower = min(tLims)
    tUpper = max(tLims)

    lines = []
    for aSeg in lineSegs :
        mask = np.logical_and(tUpper >= aSeg['frameNums'],
                              tLower <= aSeg['frameNums'])
	lines.append(axis.plot(aSeg['xLocs'][mask], aSeg['yLocs'][mask],
			       **kwargs)[0])

    return lines

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
            corners.append(axis.scatter(aVol['stormCells']['xLocs'],
                                        aVol['stormCells']['yLocs'], s=1, **kwargs))
    return corners

class CornerAnimation(FuncAnimation) :
    def __init__(self, figure, frameCnt, **kwargs) :
        self._allcorners = []
        self._flatcorners = []
        self._myframeCnt = frameCnt

        FuncAnimation.__init__(self, figure, self.update_corners,
                                     frameCnt, fargs=(self._allcorners,),
                                     **kwargs)

    def update_corners(self, idx, corners) :
        for index, scatterCol in enumerate(zip(*corners)) :
            for aCollection in scatterCol :
                aCollection.set_visible(index == idx)
            
        return self._flatcorners

    def AddCornerVolume(self, corners) :
        if len(corners) > self._myframeCnt :
            self._myframeCnt = len(corners)
        self._allcorners.append(corners)
        self._flatcorners.extend(corners)

    def _init_draw(self) :
        for aColl in self._flatcorners :
            aColl.set_visible(False)

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
            mask = np.logical_and(aSeg['frameNums'] <= theHead,
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
def PrepareFrameLims1(f) :
    def wrapf(tracks1, startFrame=None, endFrame=None, **kwargs) :
        if startFrame is None or endFrame is None :
            trackFrames = [aTrack['frameNums'] for aTrack in tracks1]
            if startFrame is None : startFrame = min([min(aTrack) for aTrack in trackFrames if len(aTrack) > 0])
            if endFrame is None : endFrame = max([max(aTrack) for aTrack in trackFrames if len(aTrack) > 0])

        return f(tracks1, startFrame, endFrame, **kwargs)
    return wrapf
            
def PrepareFrameLims2(f) :
    def wrapf(tracks1, tracks2, startFrame=None, endFrame=None, **kwargs) :
        if startFrame is None or endFrame is None :
            trackFrames = [aTrack['frameNums'] for aTrack in tracks1 + tracks2]
            if startFrame is None : startFrame = min([min(aTrack) for aTrack in trackFrames if len(aTrack) > 0])
            if endFrame is None : endFrame = max([max(aTrack) for aTrack in trackFrames if len(aTrack) > 0])

        return f(tracks1, tracks2, startFrame, endFrame, **kwargs)
    return wrapf
 

@PrepareFrameLims1
def PlotTrack(tracks, startFrame=None, endFrame=None, axis=None, **kwargs) :
    if axis is None :
        axis = plt.gca()

    lines = []
    for aTrack in tracks :
        mask = np.logical_and(aTrack['frameNums'] <= endFrame,
                              aTrack['frameNums'] >= startFrame)
        lines.append(axis.plot(aTrack['xLocs'][mask], aTrack['yLocs'][mask],
                     **kwargs)[0])

    return lines


           

@PrepareFrameLims2
def PlotTracks(true_tracks, model_tracks, startFrame=None, endFrame=None,
               axis=None, animated=False) :
    if axis is None :
        axis = plt.gca()

    trueLines = PlotTrack(true_tracks, startFrame, endFrame,
                          marker='.', markersize=9.0,
                          color='grey', linewidth=2.5, linestyle=':', 
                          animated=False, zorder=1, axis=axis)
    modelLines = PlotTrack(model_tracks, startFrame, endFrame, 
                           marker='.', markersize=8.0, 
                           color='r', linewidth=2.5, alpha=0.55, 
                           zorder=2, animated=animated, axis=axis)
    return {'trueLines': trueLines, 'modelLines': modelLines}

@PrepareFrameLims2
def PlotPlainTracks(tracks, falarms,
                    startFrame=None, endFrame=None,
                    axis=None, animated=False) :
    if axis is None :
        axis = plt.gca()

    trackLines = PlotTrack(tracks, startFrame, endFrame, axis=axis, marker='.', markersize=6.0,
                           color='k', linewidth=1.5, animated=animated)
    falarmLines = PlotTrack(falarms, startFrame, endFrame, axis=axis, marker='.', markersize=6.0,
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
    theLines = PlotTracks(true_tracks, model_tracks, startFrame, endFrame, 
                          axis=axis, animated=True)

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
    theLines = PlotPlainTracks(tracks, falarms, startFrame, endFrame,
                               axis=axis, animated=True)

    return AnimateLines(theLines['trackLines'] + theLines['falarmLines'],
                        tracks + falarms, startFrame, endFrame,
                        axis=axis, figure=figure, event_source=event_source, **kwargs)



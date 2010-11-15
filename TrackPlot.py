#------------------------
# for the animation code
#import gtk, gobject

#import matplotlib
#matplotlib.use('GTKAgg')
from matplotlib.animation import FuncAnimation
#------------------------

import numpy
import matplotlib.pyplot as pyplot
import matplotlib.collections as mcoll

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
        mask = numpy.logical_and(tUpper >= aSeg['t'],
                                 tLower <= aSeg['t'])
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

def Animate_Segments(truthTable, frameCnt, tLims, axis=None, figure=None, event_source=None, **kwargs) :
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

    return AnimateLines(theLines, theSegs, frameCnt, min(tLims), max(tLims), axis=axis, figure=figure, event_source=None, **kwargs)

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
        else :
            # an empty circle collection
            corners.append(mcoll.CircleCollection([], offsets=zip([], [])))

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
def AnimateLines(lines, lineData, frameCnt, startT, endT, 
                 figure=None, axis=None,
                 speed=1.0, loop_hold=2.0, tail=None, event_source=None) :
    # TODO: get speed and loop_hold compatible with FuncAnimation

    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    if tail is None :
        tail = endT - startT

    times = numpy.linspace(startT, endT, frameCnt, endpoint=True) 

    def update_lines(idx, lineData, lines, times, startT, endT, tail) :
        theHead = times[numpy.clip(idx, 0, len(times) - 1)]
        startTail = max(theHead - tail, startT)
            
        for (index, (line, aSeg)) in enumerate(zip(lines, lineData)) :
            mask = numpy.logical_and(aSeg['t'] <= theHead,
                                     aSeg['t'] >= startTail)
		
            line.set_xdata(aSeg['xLocs'][mask])
            line.set_ydata(aSeg['yLocs'][mask])
        return lines

    return FuncAnimation(figure, update_lines, frameCnt,
                         fargs=(lineData, lines, times, startT, endT, tail),
                         interval=500, blit=True, event_source=event_source)


###################################################
#		Track Plotting                            #
###################################################
def PlotTrack(tracks, tLims, axis=None, **kwargs) :
    if axis is None :
        axis = pyplot.gca()

    startT = min(tLims)
    endT = max(tLims)

    lines = []
    for aTrack in tracks :
        mask = numpy.logical_and(aTrack['t'] <= endT,
                                 aTrack['t'] >= startT)
        lines.append(axis.plot(aTrack['xLocs'][mask], aTrack['yLocs'][mask],
			       **kwargs)[0])

    return lines



def PlotTracks(true_tracks, model_tracks, tLims, startT=None, endT=None,
	       axis=None, animated=False) :
    if axis is None :
        axis = pyplot.gca()

    if startT is None : startT = min(tLims)
    if endT is None : endT = max(tLims)

    trueLines = PlotTrack(true_tracks, tLims,
			  marker='.', markersize=9.0,
			  color='grey', linewidth=2.5, linestyle=':', 
			  animated=False, zorder=1, axis=axis)
    modelLines = PlotTrack(model_tracks, (startT, endT), 
			   marker='.', markersize=8.0, 
			   color='r', linewidth=2.5, alpha=0.55, 
			   zorder=2, animated=animated, axis=axis)
    return {'trueLines': trueLines, 'modelLines': modelLines}

def PlotPlainTracks(tracks, falarms, tLims, startT=None, endT=None, axis=None, animated=False) :
    if axis is None :
        axis = pyplot.gca()

    if startT is None : startT = min(tLims)
    if endT is None : endT = max(tLims)

    trackLines = PlotTrack(tracks, tLims, axis=axis, marker='.', markersize=6.0,
                           color='k', linewidth=1.5, animated=animated)
    falarmLines = PlotTrack(falarms, tLims, axis=axis, marker='.', markersize=6.0,
                            linestyle=' ', color='r', animated=animated)

    return {'trackLines': trackLines, 'falarmLines': falarmLines}



def Animate_Tracks(true_tracks, model_tracks, frameCnt, tLims, 
                   axis=None, figure=None, event_source=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    startT = min(tLims)
    endT = max(tLims)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, tLims, 
                          startT, endT, axis=axis, animated=True)

    return AnimateLines(theLines['trueLines'] + theLines['modelLines'],
                        true_tracks + model_tracks, frameCnt, startT, endT,
                        axis=axis, figure=figure, event_source=event_source, **kwargs)


def Animate_PlainTracks(tracks, falarms, frameCnt, tLims, figure=None,
                        axis=None, event_source=None, **kwargs) :
    if figure is None :
        figure = pyplot.gcf()

    if axis is None :
        axis = figure.gca()

    startT = min(tLims)
    endT = max(tLims)

    # Create the initial lines
    theLines = PlotPlainTracks(tracks, falarms, tLims,
                               startT, endT, axis=axis, animated=False)

    return AnimateLines(theLines['trackLines'] + theLines['falarmLines'],
                        tracks + falarms, frameCnt, startT, endT,
                        axis=axis, figure=figure, event_source=event_source, **kwargs)



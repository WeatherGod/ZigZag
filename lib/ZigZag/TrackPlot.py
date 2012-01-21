
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#################################
#		Segment Plotting        #
#################################
def PlotSegment(lineSegs, fLims, axis=None, **kwargs) :
    if axis is None :
       axis = plt.gca()

    fLower = min(fLims)
    fUpper = max(fLims)

    lines = []
    for aSeg in lineSegs :
        mask = np.logical_and(fUpper >= aSeg['frameNums'],
                              fLower <= aSeg['frameNums'])
	lines.append(axis.plot(aSeg['xLocs'][mask], aSeg['yLocs'][mask],
			       **kwargs)[0])

    return lines

def PlotSegments(truthTable, fLims, axis=None, width=4.0, **kwargs) :
    tableSegs = {}

    # Correct Stuff
    tableSegs['assocs_Correct'] = PlotSegment(truthTable['assocs_Correct'],
                                              fLims, axis,
                                              linewidth=width, color= 'green',
                                              marker=' ',
                                              zorder=1, **kwargs)
    tableSegs['falarms_Correct'] = PlotSegment(truthTable['falarms_Correct'],
                                               fLims, axis,
                                               color='lightgreen',
                                               linestyle=' ',
                                               marker='.', markersize=2*width,
                                               zorder=1, **kwargs)

    # Wrong Stuff
    tableSegs['falarms_Wrong'] = PlotSegment(truthTable['falarms_Wrong'],
                                             fLims, axis,
                                             linewidth=width, color='gray',
                                             linestyle='-.',
                                             dash_capstyle = 'round',
                                             marker=' ', #markersize = 2*width,
                                             zorder=2, **kwargs)
    tableSegs['assocs_Wrong'] = PlotSegment(truthTable['assocs_Wrong'],
                                            fLims, axis,
                                            linewidth=width, color='red',
                                            marker=' ',
                                            zorder=2, **kwargs)

    return tableSegs

def Animate_Segments(truthTable, fLims, axis=None, **kwargs) :
    tableLines = PlotSegments(truthTable, fLims, axis=axis, animated=False) 

    theLines = []
    theSegs = []

    for keyname in tableLines :
        theLines += tableLines[keyname]
        theSegs += truthTable[keyname]

    return theLines, theSegs

#############################################
#           Corner Plotting                 #
#############################################
def PlotCorners(volData, tLims, axis=None, **kwargs) :
    if axis is None :
        axis = plt.gca()

    corners = []
    startT = min(tLims)
    endT = max(tLims)
    for aVol in volData :
        if startT <= aVol['volTime'] <= endT :
            corners.append(axis.scatter(aVol['stormCells']['xLocs'],
                                        aVol['stormCells']['yLocs'],
                                        s=1, c='k',
                                        **kwargs))
    return corners

#############################################
#           Animation Code                  #
#############################################
class CornerAnimation(FuncAnimation) :
    def __init__(self, figure, frameCnt, tail=0, **kwargs) :
        """
        Create an animation of the 'corners' (the centroids of detections).

        *figure*            The matplotlib Figure object
        *frameCnt*          The number of frames for the animation loop
        *tail*              The number of frames to hold older corners

        All other :class:`FuncAnimation` kwargs are available.

        TODO: Add usage information.
        """
        self._allcorners = []
        self._flatcorners = []
        self._myframeCnt = frameCnt

        FuncAnimation.__init__(self, figure, self.update_corners,
                                     frameCnt, fargs=(self._allcorners, tail),
                                     **kwargs)

    def update_corners(self, idx, corners, tail) :
        for index, scatterCol in enumerate(zip(*corners)) :
            for aCollection in scatterCol :
                aCollection.set_visible((idx - tail) <= index <= idx)

        return self._flatcorners

    def AddCornerVolume(self, corners) :
        if len(corners) > self._myframeCnt :
            self._myframeCnt = len(corners)
        self._allcorners.append(corners)
        self._flatcorners.extend(corners)

    def _init_draw(self) :
        for aColl in self._flatcorners :
            aColl.set_visible(False)


class SegAnimator(FuncAnimation) :
    def __init__(self, fig, startFrame, endFrame, tail, **kwargs) :
        """
        Create an animation of track segments.

        *fig*               matplotlib Figure object
        *startFrame*        The frame number to start animation loop at
        *endFrame*          The frame number to end the loop at
        *tail*              How many frames to keep older segments in view

        All other :class:`FuncAnimation` constructor  kwargs are available
        except *frames* and *fargs*.

        TODO: Add usage info.
        """
        self._lineData = []
        self._lines = []
        if 'frames' in kwargs :
            raise KeyError("Do not specify 'frames' for the constructor"
                           " of SegAnimator")

        FuncAnimation.__init__(self, fig, self.update_lines,
                                     endFrame - startFrame + 1,
                                     fargs=(self._lineData, self._lines,
                                            startFrame, endFrame, tail),
                                     **kwargs)

    def update_lines(self, idx, lineData, lines, firstFrame, lastFrame, tail) :
        theHead = min(idx + firstFrame, lastFrame)
        startTail = max(theHead - tail, firstFrame)

        for (index, (line, aSeg)) in enumerate(zip(lines, lineData)) :
            mask = np.logical_and(aSeg['frameNums'] <= theHead,
                                  aSeg['frameNums'] >= startTail)

            line.set_xdata(aSeg['xLocs'][mask])
            line.set_ydata(aSeg['yLocs'][mask])
        return lines

###################################################
#		Track Plotting                            #
###################################################
def PrepareFrameLims1(f) :
    def wrapf(tracks1, startFrame=None, endFrame=None, **kwargs) :
        if startFrame is None or endFrame is None :
            trackFrames = [aTrack['frameNums'] for aTrack in tracks1]
            if startFrame is None :
                startFrame = min([min(aTrack) for aTrack in trackFrames if
                                  len(aTrack) > 0])
            if endFrame is None :
                endFrame = max([max(aTrack) for aTrack in trackFrames if
                                len(aTrack) > 0])

        return f(tracks1, startFrame, endFrame, **kwargs)
    return wrapf
            
def PrepareFrameLims2(f) :
    def wrapf(tracks1, tracks2, startFrame=None, endFrame=None, **kwargs) :
        if startFrame is None or endFrame is None :
            trackFrames = [aTrack['frameNums'] for aTrack in tracks1 + tracks2]
            if startFrame is None :
                startFrame = min([min(aTrack) for aTrack in trackFrames if
                                  len(aTrack) > 0])
            if endFrame is None :
                endFrame = max([max(aTrack) for aTrack in trackFrames if
                                len(aTrack) > 0])

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
                          animated=animated, zorder=1, axis=axis)
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

    trackLines = PlotTrack(tracks, startFrame, endFrame, axis=axis, marker='.',
                           markersize=6.0, color='k', linewidth=1.5,
                           animated=animated)
    falarmLines = PlotTrack(falarms, startFrame, endFrame, axis=axis,
                            marker='.', markersize=6.0, linestyle=' ',
                            color='r', animated=animated)

    return {'trackLines': trackLines, 'falarmLines': falarmLines}



def Animate_Tracks(true_tracks, model_tracks, fLims, axis=None) :
    startFrame = min(fLims)
    endFrame = max(fLims)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, startFrame, endFrame, 
                          axis=axis, animated=False)

    return (theLines['trueLines'] + theLines['modelLines'],
            true_tracks + model_tracks)

def Animate_PlainTracks(tracks, falarms, fLims, axis=None) :
    startFrame = min(fLims)
    endFrame = max(fLims)

    # Create the initial lines
    theLines = PlotPlainTracks(tracks, falarms, startFrame, endFrame,
                               axis=axis, animated=False)

    return (theLines['trackLines'] + theLines['falarmLines'],
            tracks + falarms)

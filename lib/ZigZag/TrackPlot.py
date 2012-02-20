
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#################################
#		Segment Plotting        #
#################################
def PlotSegment(lineSegs, fLims, axis=None, fade=False, **kwargs) :
    if axis is None :
       axis = plt.gca()

    fLower = min(fLims)
    fUpper = max(fLims)

    lines = []
    for aSeg in lineSegs :
        mask = np.logical_and(fUpper >= aSeg['frameNums'],
                              fLower <= aSeg['frameNums'])
        if fade :
            head = aSeg['frameNums'].max()
            make_alpha = max(min(1.0 - (float(fUpper - head) /
                                        (fUpper - fLower + 1)), 1.0), 0.0)
        else :
            make_alpha = 1.0

        lines.append(axis.plot(aSeg['xLocs'][mask], aSeg['yLocs'][mask],
                               alpha=make_alpha, **kwargs)[0])

    return lines

seg_colors = dict(assocs_Correct='green',
                  falarms_Correct='lightgreen',
                  falarms_Wrong='grey',
                  assocs_Wrong='red')

seg_marker = dict(assocs_Correct=' ',
                  falarms_Correct='.',
                  falarms_Wrong=' ',
                  assocs_Wrong=' ')

seg_linestyle = dict(assocs_Correct='-',
                     falarms_Correct=' ',
                     falarms_Wrong='--',
                     assocs_Wrong='-')

seg_zorder = dict(assocs_Correct=1,
                  falarms_Correct=1,
                  falarms_Wrong=2,
                  assocs_Wrong=2)

def PlotSegments(truthTable, fLims, axis=None, width=4.0,
                 fade=False, **kwargs) :
    tableSegs = {}

    for segType in ['assocs_Correct', 'falarms_Correct',
                    'falarms_Wrong', 'assocs_Wrong'] :
        tableSegs[segType] = PlotSegment(truthTable[segType], fLims, axis,
                                         linewidth=width, fade=fade,
                                         color=seg_colors[segType],
                                         zorder=seg_zorder[segType],
                                         linestyle=seg_linestyle[segType],
                                         marker=seg_marker[segType],
                                         dash_capstyle='round',
                                         **kwargs)
    return tableSegs

def Animate_Segments(truthTable, fLims, axis=None, fade=False, **kwargs) :
    tableLines = PlotSegments(truthTable, fLims, axis=axis, fade=fade,
                              animated=False)

    theLines = []
    theSegs = []

    for keyname in tableLines :
        theLines += tableLines[keyname]
        theSegs += truthTable[keyname]

    return theLines, theSegs

#############################################
#           Corner Plotting                 #
#############################################
def PlotCorners(volData, tLims, axis=None, fade=False, big=False, **kwargs) :
    if axis is None :
        axis = plt.gca()

    cornerStyle = (dict(s=1, c='k') if not big else
                   dict(s=10, facecolor='c', edgecolor='k'))
    # This approach allows the user to override the above styles
    cornerStyle.update(kwargs)

    corners = []
    startT = min(tLims)
    endT = max(tLims)
    for aVol in volData :
        if startT <= aVol['volTime'] <= endT :
            if fade :
                make_alpha = max(min(1.0 - (float(endT - aVol['volTime']) /
                                            (endT - startT)), 1.0), 0.0)
            else :
                make_alpha = 1.0
            corners.append(axis.scatter(aVol['stormCells']['xLocs'],
                                        aVol['stormCells']['yLocs'],
                                        alpha=make_alpha,
                                        **cornerStyle))
    return corners

#############################################
#           Animation Code                  #
#############################################
class CornerAnimation(FuncAnimation) :
    def __init__(self, figure, frameCnt, tail=0, fade=False, **kwargs) :
        """
        Create an animation of the 'corners' (the centroids of detections).

        *figure*            The matplotlib Figure object
        *frameCnt*          The number of frames for the animation loop
        *tail*              The number of frames to hold older corners
        *fade*              Whether to fade older features (default: False).

        All other :class:`FuncAnimation` kwargs are available.

        TODO: Add usage information.
        """
        self._allcorners = []
        self._flatcorners = []
        self._myframeCnt = frameCnt
        self.fade = fade

        FuncAnimation.__init__(self, figure, self.update_corners,
                                     frameCnt, fargs=(self._allcorners, tail),
                                     **kwargs)

    def update_corners(self, idx, corners, tail) :
        for index, scatterCol in enumerate(zip(*corners)) :
            make_vis = ((idx - tail) <= index <= idx)
            make_alpha = max(min(1.0 - ((idx - index) / (tail + 1.)), 1.0), 0.0)
            for aCollection in scatterCol :
                aCollection.set_visible(make_vis)
                if self.fade :
                    aCollection.set_alpha(make_alpha)

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
    def __init__(self, fig, startFrame, endFrame, tail, fade=False, **kwargs) :
        """
        Create an animation of track segments.

        *fig*               matplotlib Figure object
        *startFrame*        The frame number to start animation loop at
        *endFrame*          The frame number to end the loop at
        *tail*              How many frames to keep older segments in view
        *fade*              Whether or not to fade track tails for
                            non-active tracks (default: False).

        All other :class:`FuncAnimation` constructor  kwargs are available
        except *frames* and *fargs*.

        TODO: Add usage info.
        """
        self._lineData = []
        self._lines = []
        if 'frames' in kwargs :
            raise KeyError("Do not specify 'frames' for the constructor"
                           " of SegAnimator")

        self.fade = fade

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
            if self.fade :
                last = aSeg['frameNums'].max()
                line.set_alpha(max(min(1.0 - ((theHead - last) / (tail + 1.)),
                                      1.0), 0.0))
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
def PlotTrack(tracks, startFrame=None, endFrame=None, axis=None, fade=False,
              **kwargs) :
    if axis is None :
        axis = plt.gca()

    lines = []
    for aTrack in tracks :
        mask = np.logical_and(aTrack['frameNums'] <= endFrame,
                              aTrack['frameNums'] >= startFrame)
        if fade :
            head = aTrack['frameNums'].max()
            make_alpha = max(min(1.0 - (float(endFrame - head) /
                                        (endFrame - startFrame + 1)), 1.0),
                             0.0)
        else :
            make_alpha = 1.0

        lines.append(axis.plot(aTrack['xLocs'][mask], aTrack['yLocs'][mask],
                               alpha=make_alpha, **kwargs)[0])

    return lines


@PrepareFrameLims2
def PlotTracks(true_tracks, model_tracks, startFrame=None, endFrame=None,
               axis=None, animated=False, fade=False) :
    if axis is None :
        axis = plt.gca()

    trueLines = PlotTrack(true_tracks, startFrame, endFrame,
                          marker='.', markersize=9.0,
                          color='grey', linewidth=2.5, linestyle=':', 
                          animated=animated, zorder=1, axis=axis, fade=fade)
    modelLines = PlotTrack(model_tracks, startFrame, endFrame, 
                           marker='.', markersize=8.0, 
                           color='r', linewidth=2.5, alpha=0.55, 
                           zorder=2, animated=animated, axis=axis, fade=fade)
    return {'trueLines': trueLines, 'modelLines': modelLines}

track_props = dict(marker='.',
                   markersize=6.0,
                   color='k',
                   linewidth=1.5)

falarm_props = dict(marker='.',
                    markersize=6.0,
                    linestyle=' ',
                    color='r')
@PrepareFrameLims2
def PlotPlainTracks(tracks, falarms,
                    startFrame=None, endFrame=None,
                    axis=None, animated=False, fade=False) :
    if axis is None :
        axis = plt.gca()

    trackLines = PlotTrack(tracks, startFrame, endFrame, axis=axis,
                           animated=animated, fade=fade, **track_props)
    falarmLines = PlotTrack(falarms, startFrame, endFrame, axis=axis,
                            animated=animated, fade=fade, **falarm_props)

    return {'trackLines': trackLines, 'falarmLines': falarmLines}



def Animate_Tracks(true_tracks, model_tracks, fLims, axis=None, fade=False) :
    startFrame = min(fLims)
    endFrame = max(fLims)

    # create the initial lines    
    theLines = PlotTracks(true_tracks, model_tracks, startFrame, endFrame, 
                          axis=axis, animated=False, fade=fade)

    return (theLines['trueLines'] + theLines['modelLines'],
            true_tracks + model_tracks)

def Animate_PlainTracks(tracks, falarms, fLims, axis=None, fade=False) :
    startFrame = min(fLims)
    endFrame = max(fLims)

    # Create the initial lines
    theLines = PlotPlainTracks(tracks, falarms, startFrame, endFrame,
                               axis=axis, animated=False, fade=fade)

    return (theLines['trackLines'] + theLines['falarmLines'],
            tracks + falarms)

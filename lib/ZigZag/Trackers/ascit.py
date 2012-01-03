from ZigZag.TrackUtils import volume_dtype, tracking_dtype, identifier_dtype
import numpy as np
import numpy.lib.recfunctions as nprf   # for append_fields()
from scikits.learn.utils.hungarian import _Hungarian
from collections import defaultdict

class ASCIT(object) :
    """
    An object for performing a modified version of the tracking portion of
    the SCIT algorithm.

    *distThresh* is the maximum distance storms are expected to travel
                 in the frame intervals.
    """
    _fallback_cost = 999999.0

    def __init__(self, distThresh=5.0, framesBack=10) :
        self.distThresh = distThresh
        self._highCost = None
        self._frames_back = framesBack

        # If the cost threshold is set larger than
        # the fallback cost, then nothing works right
        assert(distThresh < ASCIT._fallback_cost)

        self.reinit_tracker()

    def reinit_tracker(self) :
        """
        Reinitialize the TITAN tracker for a new set of storm cells
        to track.
        """
        self.stateHist = []
        self.tracks = []
        self.prevStorms = {}
        self._currCells = []
        self._fcasts = np.array([], dtype=[('xLocs', 'f4'), ('yLocs', 'f4')])
        self.ellipses = []

    def _calc_cost(self, t0_strms, t1_strms) :
        x0 = t0_strms['xLocs']
        x1 = t1_strms['xLocs']

        y0 = t0_strms['yLocs']
        y1 = t1_strms['yLocs']

        C = np.hypot(x0[:, np.newaxis] - x1[np.newaxis, :],
                     y0[:, np.newaxis] - y1[np.newaxis, :])

        # Make sure the highcost is gonna be high enough
        # The total cost is going to be the sum of costs over
        # the assignments.  Since there will be at most min(C.shape)
        # assignments, then multiplying the number of possible assignments
        # by the maximum assignment cost should guarantee a high enough cost.
        # Multiplying by 10 is just for extra measure.
        self._highCost = ((10 * (min(C.shape) * C.max()))
                          if C.size > 0 else ASCIT._fallback_cost)

        # Just double-checking that _highCost will pass 
        # the reject_assoc() later.
        if not self._reject_assoc(self._highCost) :
            # TODO: Need better safety here... I would likely prefer
            #  np.inf, maybe.
            # New NOTE: Because that wasn't good enough to satisfy
            #  _reject_assoc(), go back to the fall-back of 999999.
            self._highCost = ASCIT._fallback_cost

        # For any possible association where the points are too far
        # apart, then return a very large value.  Otherwise, return
        # the calculated cost for that association.
        return np.where(self._reject_assoc(C), self._highCost, C)

    def _reject_assoc(self, dist_val) :
        """ Reject this association because they were too far apart """
        return dist_val >= self.distThresh

    def _process_assocs(self, assocs, cost, prevStrmCnt, currStrmCnt) :
        strms_end = {}
        strms_start = {}
        strms_keep = {}

        # IMPORTANT: I am creating a mask rather than doing the comparison
        #  within the loop because of numpy-casting issues.  Because *cost*
        #  could have a dtype of "float" and self._highCost is a numpy float,
        #  the type casting is different if I do element-wise comparison 
        # versus direct element-based comparisons
        mask = (cost == self._highCost)

        for t0_index, t1_index in assocs :
            if mask[t0_index, t1_index] :
                # Because of the rejection, split this
                # association into the termination of
                # one track and the start of a new track
                strms_end[t0_index] = self.prevStorms[t0_index]
                # TrackID will be assigned when the track is created
                strms_start[t1_index] = None
            else :
                if cost[t0_index, t1_index] > self._highCost :
                    print "SHOULD HAVE BEEN REJECTED!", \
                          cost[t0_index, t1_index] - self._highCost
                strms_keep[t1_index] = self.prevStorms[t0_index]

        # Determine which other current storms were not associated
        # This happens when there are more current storms than previous storms
        newstorms = set(range(currStrmCnt)) - (set(strms_start.keys()) |
                                               set(strms_keep.keys()))
        strms_start.update(zip(newstorms, [None]*len(newstorms)))

        # Determine which other previous storms were not associated
        # This happens when there are more previous storms than current storms
        deadstorms = (set(range(prevStrmCnt)) -
                      set([t0_index for t0_index, t1_index in assocs]))
        strms_end.update([(t0_index, self.prevStorms[t0_index]) for
                          t0_index in deadstorms])

        return strms_end, strms_keep, strms_start



    def _update_tracks(self, currStrms, currFrame, assocs,
                       strms_end, strms_keep, strms_start) :
        """
        *strms_end*     dict of storm indices for storms at index-1 with
                        value trackID
        *strms_keep*    dict of storm indices for storms at index with
                        value trackID
        *strms_start*   dict of storm indices for storms at index with
                        value trackID
        """
        # Only need to do the following if adding or extending
        # existing tracks
        if len(strms_keep) > 0 or len(strms_start) > 0 :
            # The volume data has only xLocs and yLocs,
            # so we need to add some track-relevant fields
            # to the data without modifying the input data.
            strmCnt = len(currStrms)
            currStrms = nprf.append_fields(currStrms,
                                           ('st_xLocs', 'st_yLocs',
                                            'frameNums', 'types', 'trackID'),
                                           ([np.nan] * strmCnt,
                                            [np.nan] * strmCnt,
                                            [currFrame] * strmCnt,
                                            ['U'] * strmCnt,
                                            [-1] * strmCnt),
                                           dtypes=[dtype[1] for dtype in
                                                   (tracking_dtype +
                                                    identifier_dtype)],
                                           usemask=False)

        assoc_dict = {curr:prev for prev, curr in assocs}

        for strmID, trackID in strms_keep.iteritems() :
            currStrms[strmID]['trackID'] = trackID
            t0_index = assoc_dict[strmID]
            # The "state-estimated" position for this track will be the
            # position that would result in a zero-cost for the position
            # portion of the cost function.
            currStrms[strmID]['st_xLocs'] = self._fcasts['xLocs'][t0_index]
            currStrms[strmID]['st_yLocs'] = self._fcasts['yLocs'][t0_index]

            # Update the last storm cell listed in the track as matched
            self.tracks[trackID]['types'][-1] = 'M'
            # A poor-man's append for numpy arrays...
            self.tracks[trackID] = np.hstack((self.tracks[trackID],
                                              currStrms[strmID]))

        for strmID in strms_start.keys() :
            # Get the next available track ID number
            trackID = len(self.tracks)

            # Provide a trackID for the strms_start dictionary
            # and the stormcell itself.
            strms_start[strmID] = trackID
            currStrms[strmID]['trackID'] = trackID

            # Because it is a new track, there is no forecasted
            # position.  Therefore, the state-estimated location
            # will be the same as the reported location.
            currStrms[strmID]['st_xLocs'] = currStrms[strmID]['xLocs']
            currStrms[strmID]['st_yLocs'] = currStrms[strmID]['yLocs']

            # Add this new track to the list.
            self.tracks.append(np.array([currStrms[strmID]],
                                        dtype=volume_dtype))

        # Mark any length-1 tracks for strms_end as False Alarms
        for trackID in strms_end.values() :
            if len(self.tracks[trackID]) == 1 :
                self.tracks[trackID]['types'][-1] = 'F'
            else :
                self.tracks[trackID]['types'][-1] = 'M'

    def TrackStep(self, volume_data) :
        """
        Perform tracking with a new frame of data.

        *volume_data*       TODO
        """
        if len(self.stateHist) > 0 :
            self._prevCells = self.stateHist[-1]['stormCells']
            dT = volume_data['frameNum'] - self.stateHist[-1]['frameNum']
        else :
            self._prevCells = np.array([], dtype=volume_dtype)
            dT = 0

        self._currCells = volume_data['stormCells']
        frameNum = volume_data['frameNum']

        self.stateHist.append({'volTime': volume_data['volTime'],
                               'frameNum': volume_data['frameNum'],
                               'stormCells': volume_data['stormCells']})



        C = self._calc_cost(self._fcasts, self._currCells)
        H = _Hungarian()
        # Returns a list of (row, col) tuples
        assocs = H.compute(C)

        # Return the storms organized by their status.
        # strms_end  :  dict of storm indices for storms at index-1 with
        #               value trackID
        # strms_keep :  dict of storm indices for storms at index with
        #               value trackID
        # strms_start:  dict of storm indices for storms at index with
        #               value trackID
        strms_end, strms_keep, strms_start = self._process_assocs(assocs,
                                        C, len(self._prevCells),
                                           len(self._currCells))

        self._update_tracks(self._currCells, frameNum, assocs,
                            strms_end, strms_keep, strms_start)

        # The union of tracks that were kept and started for the next loop
        # iteration. This is used extensively throughout _process_assocs()
        # and finalize().
        self.prevStorms = dict(strms_keep, **strms_start)
        strmIDs, trckIDs = (zip(*self.prevStorms.items()) if
                                len(self.prevStorms) > 0 else
                            ((), ()))

        self._fcasts, _ = self.forecast_tracks(dT, trckIDs)

        return strms_end, strms_keep, strms_start

    def forecast_tracks(self, deltaT, trackIDs) :
        frames_back = self._frames_back

        fcasts = [None] * len(trackIDs)
        trends = [None] * len(trackIDs)

        tot_x_spd = 0.0
        tot_y_spd = 0.0
        trackCnt = 0

        for fIndex, trackIndex in enumerate(trackIDs) :
            track = self.tracks[trackIndex][-frames_back:]

            if len(track) <= 1 :
                continue

            # Grab only the variables you want for at most the past
            # *frames_back* frames.
            x = track[['xLocs', 'yLocs']]
            t = track['frameNums'].astype(float)

            xAvg = np.mean(x['xLocs'])
            yAvg = np.mean(x['yLocs'])
            tAvg = np.mean(t)

            tDev = t - tAvg
            xtVar = np.sum((x['xLocs'] - xAvg) * tDev)
            ytVar = np.sum((x['yLocs'] - yAvg) * tDev)
            ttVar = np.sum(tDev**2)

            x_spd = xtVar / ttVar
            y_spd = ytVar / ttVar

            tot_x_spd += x_spd
            tot_y_spd += y_spd
            trackCnt += 1

            trends[fIndex] = (x_spd, y_spd)

        if trackCnt != 0 :
            systemAvg = (tot_x_spd / trackCnt,
                         tot_y_spd / trackCnt)
        else :
            systemAvg = (0.0, 0.0)

        # Any newly established tracks will be initialized
        # with the average speed of all the existing tracks
        # Also perform all final forecasts.
        for fIndex, trckID in enumerate(trackIDs) :
            if trends[fIndex] is None :
                trends[fIndex] = systemAvg

            fcasts[fIndex] = (self.tracks[trckID]['xLocs'][-1] +
                               trends[fIndex][0] * deltaT,
                              self.tracks[trckID]['yLocs'][-1] +
                               trends[fIndex][1] * deltaT)
        return (np.array(fcasts, dtype=[('xLocs', 'f4'), ('yLocs', 'f4')]),
                np.array(trends, dtype=[('xLocs', 'f4'), ('yLocs', 'f4')]))

    @staticmethod
    def reverse_lookup(strms_end, strms_keep, strms_start) :
        """
        Create reverse lookup dictionaries for the resulting dictionaries from
        self.TrackStep().
        """
        return ({trackID:strmID for strmID, trackID in strms_end.iteritems()},
                {trackID:strmID for strmID, trackID in strms_keep.iteritems()},
                {trackID:strmID for strmID, trackID in strms_start.iteritems()})

    def finalize(self) :
        """
        Used to finalize the track data when there are no more
        frames to process.

        You can always view the self.track data member, but this
        function will perform any last tidying up.
        """
        self._update_tracks(None, None, [], self.prevStorms, {}, {})


if __name__ == '__main__' :
    import os.path
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

    from ZigZag.TrackPlot import PlotPlainTracks, PlotSegments
    from ZigZag.TrackUtils import CleanupTracks, FilterMHTTracks,\
                                  CreateSegments, CompareSegments
    from ZigZag.TrackFileUtils import ReadCorners, ReadTracks

    dirPath = "/home/ben/Programs/Tracking/NewSim1"
    #dirPath = "/home/bvr/TrackingStudy/SquallSim"
    cornerVol = ReadCorners(os.path.join(dirPath, "InputDataFile"),
                            dirPath)['volume_data']

    true_tracks, true_falarms = FilterMHTTracks(*ReadTracks(os.path.join(
                                                    dirPath, "noise_tracks")))

    frameLims = (0, len(cornerVol))
    print frameLims[1]

    t = ASCIT(distThresh=5)

    for aVol in cornerVol :
        t.TrackStep(aVol)

    t.finalize()

    tracks = t.tracks
    falarms = []
    CleanupTracks(tracks, falarms)

    # Compare with "truth data"
    segs = [CreateSegments(trackData) for trackData in (true_tracks,
                                                        true_falarms,
                                                        tracks, falarms)]
    truthtable = CompareSegments(*segs)


    # Display Result
    fig = plt.figure(figsize=plt.figaspect(0.5))
    grid = AxesGrid(fig, 111, nrows_ncols=(1, 2), aspect=False,
                    share_all=True, axes_pad=0.35)

    ax = grid[0]
    PlotPlainTracks(tracks, falarms, *frameLims, axis=ax)
    ax.set_title("ASCIT Tracks")

    ax = grid[1]
    PlotSegments(truthtable, frameLims, axis=ax)
    ax.set_title("Track Check")

    plt.show()


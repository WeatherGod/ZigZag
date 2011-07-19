from ZigZag.TrackUtils import volume_dtype, tracking_dtype, identifier_dtype
import numpy as np
import numpy.lib.recfunctions as nprf   # for append_fields()
from scikits.learn.utils.hungarian import _Hungarian

class TITAN(object) :
    """
    An object for performing the tracking portion of the TITAN algorithm
    originally designed by Mike Dixon.

    *distWeight* is the weight to apply to the distance portion of the
                 cost function. The default is to apply equal weight
                 to both distance and volume.

    *distThresh* is the maximum distance storms are expected to travel
                 in the frame intervals.
    """
    _fallback_cost = 999999.0

    def __init__(self, distWeight=0.5, distThresh=5.0) :
        self.distWeight = distWeight
        self.distThresh = distThresh
        self._highCost = None

        # If the cost threshold is set larger than
        # the fallback cost, then nothing works right
        assert(distThresh < TITAN._fallback_cost)

        self.reinit_tracker()

    @property
    def distWeight(self) :
        """
        The weight to apply to the cost function with respect to
        the centroid distances (as opposed to centroid volume).

        0 <= *distWeight* <= 1.0
        """
        return self._distWeight

    @distWeight.setter
    def distWeight(self, w) :
        if 0.0 <= w <= 1.0 :
            self._distWeight = w
        else :
            raise ValueError("Weight must be between 0.0 and 1.0")

    @property
    def volWeight(self) :
        """
        The Weight to apply to the cost function with respect to
        the centroid sizes (as opposed to centroid distances).

        0 <= *volWeight* <= 1.0
        """
        return 1.0 - self._distWeight

    @volWeight.setter
    def volWeight(self, w) :
        self.distWeight = 1.0 - w

    def reinit_tracker(self) :
        """
        Reinitialize the TITAN tracker for a new set of storm cells
        to track.
        """
        self.stateHist = []
        self.tracks = []
        self.prevStorms = {}

    def _calc_cost(self, t0_strms, t1_strms) :
        x0 = t0_strms['xLocs']
        x1 = t1_strms['xLocs']

        y0 = t0_strms['yLocs']
        y1 = t1_strms['yLocs']

        dp = np.hypot(x0[:, np.newaxis] - x1[np.newaxis, :],
                      y0[:, np.newaxis] - y1[np.newaxis, :])
        # NOTE: Mike Dixon's implementation has storm volume data, while
        #       ZigZag only has storm area.  Therefore, we will do a sqrt
        #       instead of a cubed-root.
        dv = np.abs(np.sqrt(t0_strms['sizes'][:, np.newaxis]) -
                    np.sqrt(t1_strms['sizes'][np.newaxis, :]))

        C = (self.distWeight * dp) + (self.volWeight * dv)

        # Make sure the highcost is gonna be high enough
        # The total cost is going to be the sum of costs over
        # the assignments.  Since there will be at most min(C.shape)
        # assignments, then multiplying the number of possible assignments
        # by the maximum assignment cost should guarantee a high enough cost.
        # Multiplying by 10 is just for extra measure.
        self._highCost = ((10 * (min(C.shape) * C.max()))
                          if C.size > 0 else TITAN._fallback_cost)

        # Just double-checking that _highCost will pass the reject_assoc() later.
        if not self._reject_assoc(self._highCost) :
            # TODO: Need better safety here... I would likely prefer np.inf, maybe
            # Because that wasn't good enough to satisfy _reject_assoc(),
            #   go back to the fall-back of 999999.
            self._highCost = TITAN._fallback_cost

        # For any possible association where the points are too far
        # apart, then return a very large value.  Otherwise, return
        # the calculated cost for that association.
        return np.where(self._reject_assoc(dp), self._highCost, C)

    def _reject_assoc(self, dist_val) :
        """ Reject this association because they were too far apart """
        return dist_val >= self.distThresh

    def _process_assocs(self, assocs, cost, prevStrmCnt, currStrmCnt) :
        strms_end = {}
        strms_start = {}
        strms_keep = {}

        # IMPORTANT: I am creating a mask rather than doing the comparison within
        # the loop because of numpy-casting issues.  Because *cost* could have
        # a dtype of "float" and self._highCost is a numpy float, the type casting
        # is different if I do element-wise comparison versus direct element-based
        # comparisons
        mask = (cost == self._highCost)

        for t0_index, t1_index in assocs :
            if mask[t0_index, t1_index] :
            #if cost[t0_index, t1_index] == self._highCost :
                # Because of the rejection, split this
                # association into the termination of
                # one track and the start of a new track
                strms_end[t0_index] = self.prevStorms[t0_index]
                # TrackID will be assigned when the track is created
                strms_start[t1_index] = None
            else :
                if cost[t0_index, t1_index] > self._highCost :
                    print "SHOULD HAVE BEEN REJECTED!", cost[t0_index, t1_index] - self._highCost
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

    def _update_tracks(self, currStrms, currFrame, strms_end, strms_keep, strms_start) :

        # Only need to do the following if I and adding or extending
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


        for strmID, trackID in strms_keep.iteritems() :
            currStrms[strmID]['trackID'] = trackID
            # The "state-estimated" position for this track will be the
            # position that would result in a zero-cost for the position
            # portion of the cost function (i.e., the last position in
            # the track).
            currStrms[strmID]['st_xLocs'] = self.tracks[trackID]['xLocs'][-1]
            currStrms[strmID]['st_yLocs'] = self.tracks[trackID]['yLocs'][-1]
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
            self.tracks.append(np.array([currStrms[strmID]], dtype=volume_dtype))

        # Mark any length-1 tracks for strms_end as False Alarms
        for trackID in strms_end.values() :
            if len(self.tracks[trackID]) == 1 :
                self.tracks[trackID]['types'][-1] = 'F'
            else :
                self.tracks[trackID]['types'][-1] = 'M'

    def TrackStep(self, volume_data) :
        if len(self.stateHist) > 0 :
            prevCells = self.stateHist[-1]['stormCells']
        else :
            prevCells = np.array([], dtype=volume_dtype)

        currCells = volume_data['stormCells']
        frameNum = volume_data['frameNum']

        C = self._calc_cost(prevCells, currCells)
        H = _Hungarian()
        # Returns a list of (row, col) tuples
        assocs = H.compute(C)

        # Return the storms organized by their status.
        # strms_end  :  dict of storm indices for storms at index-1 with value trackID
        # strms_keep :  dict of storm indices for storms at index with value trackID
        # strms_start:  dict of storm indices for storms at index with value trackID
        strms_end, strms_keep, strms_start = self._process_assocs(assocs, C, len(prevCells), len(currCells))

        self._update_tracks(currCells, frameNum,
                            strms_end, strms_keep, strms_start)

        # The union of tracks that were kept and started for the next loop iteration.
        self.prevStorms = strms_keep.copy()
        self.prevStorms.update(strms_start)

        self.stateHist.append({'volTime': volume_data['volTime'],
                               'frameNum': volume_data['frameNum'],
                               'stormCells': volume_data['stormCells']})

        return strms_end, strms_keep, strms_start

    def finalize(self) :
        """
        Used to finalize the track data when there are no more
        frames to process.

        You can always view the self.track data member, but this
        function will perform any last tidying up.
        """
        self._update_tracks(None, None, self.prevStorms, {}, {})


if __name__ == '__main__' :
    import os.path
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import AxesGrid

    from ZigZag.TrackPlot import PlotPlainTracks, PlotSegments
    from ZigZag.TrackUtils import CleanupTracks, FilterMHTTracks,\
                                  CreateSegments, CompareSegments
    from ZigZag.TrackFileUtils import ReadCorners, ReadTracks

    #dirPath = "/home/ben/Programs/Tracking/NewSim1"
    dirPath = "/home/bvr/TrackingStudy/SquallSim"
    cornerVol = ReadCorners(dirPath + os.path.sep + "InputDataFile",
                            dirPath)['volume_data']

    true_tracks, true_falarms = FilterMHTTracks(*ReadTracks(dirPath + os.path.sep + "noise_tracks"))

    frameLims = (0, len(cornerVol))
    print frameLims[1]

    t = TITAN(distThresh=5)

    for aVol in cornerVol :
        t.TrackStep(aVol)

    t.finalize()

    tracks = t.tracks
    falarms = []
    CleanupTracks(tracks, falarms)

    # Compare with "truth data"
    segs = [CreateSegments(trackData) for trackData in (true_tracks, true_falarms,
                                                        tracks, falarms)]
    truthtable = CompareSegments(*segs)


    # Display Result
    fig = plt.figure(figsize=plt.figaspect(0.5))
    grid = AxesGrid(fig, 111, nrows_ncols=(1, 2), aspect=False,
                    share_all=True, axes_pad=0.35)

    ax = grid[0]
    PlotPlainTracks(tracks, falarms, *frameLims, axis=ax)
    ax.set_title("TITAN Tracks")

    ax = grid[1]
    PlotSegments(truthtable, frameLims, axis=ax)
    ax.set_title("Track Check")

    plt.show()


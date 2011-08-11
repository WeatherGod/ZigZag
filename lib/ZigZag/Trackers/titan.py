from ZigZag.TrackUtils import volume_dtype, tracking_dtype, identifier_dtype
import numpy as np
import numpy.lib.recfunctions as nprf   # for append_fields()
from scikits.learn.utils.hungarian import _Hungarian
from collections import defaultdict

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
        self._currCells = []
        self.ellipses = []

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
            # TODO: Need better safety here... I would likely prefer
            #  np.inf, maybe.
            # New NOTE: Because that wasn't good enough to satisfy
            #  _reject_assoc(), go back to the fall-back of 999999.
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

    def _handle_merges(self, strms_end, strms_keep, strms_start,
                             merged_into) :
        """
        *merged_into*   dict of (strmID_1, strmID_2) pairs where strmID_1 is
                        the strmID of the storm (at current time - 1), and
                        strmID_2 is the strmID the cell merged into.
                        If strmID_2 is -1, then it did not merge into any
                        other tracks

        In the interest of maintaining the bipartite graphing framework
        used by ZigZag's analysis, each feature can only have at most
        one association going in, and one association going out.
        Therefore, we will not be fully implementing Dr. Dixon's merge/split
        handling logic with respect to translating and merging the track
        histories into one history.

        However, for each merger, we will ensure that at least one
        track gets continued (they don't always).
        """
        # Produce a dict that for each storm that a merge came from
        # have a list of storms that produced it.
        rev_lookup = defaultdict(list)
        for strmID1, strmID2 in merged_into.iteritems() :
            rev_lookup[strmID2].append(strmID1)

        # Dump those storms that never matched.  We don't care about those
        rev_lookup.pop(-1, None)

        for m_to, m_froms in rev_lookup.items() :
            # Gonna cheat here a bit.  I should be using the coordinates
            # that were used for matching, but... whatever...
            dists = [np.hypot(self._prevCells[strmID]['xLocs'] -
                               self._currCells[m_to]['xLocs'],
                              self._prevCells[strmID]['yLocs'] -
                               self._currCells[m_to]['yLocs']) for
                     strmID in m_froms]

            strm_from = m_froms[np.argmin(dists)]

            # Doing a bit of cheating here.  If *strm_from* is not in
            # *strms_end*, then that means that storm already got
            # tracked, somehow.  Now, it may be that it tracked to
            # *m_to* and all is well.
            # However, I wonder if it is possible if it could have
            # matched to a storm not listed in *m_to*? In that case,
            # then a butt-load of housekeeping needs to be done to
            # undo that association and mess things up.
            # Just skip such a scenario until we can better understand
            # the required logic.
            if strm_from not in strms_end :
                continue

            # We want to get *m_to* out of *strms_start*
            strms_start.pop(m_to, None)

            # Now, remove *strm_from* from *strms_end*.
            # If it wasn't in strms_end, then it was continued already.
            trckID = strms_end.pop(strm_from, None)

            # We need to add *m_to* to *strms_keep* if it isn't there already
            if m_to not in strms_keep :
                if trckID is None :
                    raise Exception("ERROR: Unknown trckID for merger!")
                # This should only happen if *strms_from* was in *strms_end*
                strms_keep[m_to] = trckID
            elif (trckID is not None) and strms_keep[m_to] !=  trckID :
                print "WARNING! Odd merging happened!"


    def _handle_splits(self, strms_end, strms_keep, strms_start,
                             split_from) :
        """
        *split_from*    dict of (strmID_1, strmID_2) pairs where strmID_1 is
                        the strmID of the storm that had split, and strmID_2
                        is the strmID of the storm that it had split from
                        If strmID_2 is -1, then it did not split from
                        any other storms.

        In the interest of maintaining the bipartite graphing framework
        used by ZigZag's analysis, each feature can only have at most
        one association going in, and one association going out.
        Therefore, we will not be fully implementing Dr. Dixon's merge/split
        handling logic with respect to translating and copying the track
        history into multiple histories.

        However, for each split, we will ensure that at least one
        track gets continued (they don't always).
        """
        # Produce a dict that for each storm that a split ocurred
        # from, have a list of storms that came from it.
        rev_lookup = defaultdict(list)
        for strmID1, strmID2 in split_from.iteritems() :
            rev_lookup[strmID2].append(strmID1)

        # Dump those storms that never matched.  We don't care about those
        rev_lookup.pop(-1, None)

        for s_from, s_tos in rev_lookup.items() :
            # Doing a bit of cheating here.  If *s_from* is not in
            # *strms_end*, then that means that storm already got
            # tracked, somehow.  Now, it may be that it tracked to
            # one of the *s_tos* and all is well.
            # However, I wonder if it is possible if it could have
            # matched to a storm not listed in *s_tos*? In that case,
            # then a butt-load of housekeeping needs to be done to
            # undo that association (which may undo a merging...)
            # and mess things up.
            # Just skip such a scenario until we can better understand
            # the required logic.
            if s_from not in strms_end :
                continue

            # Gonna cheat here a bit.  I should be using the coordinates
            # that were used for matching, but... whatever...
            dists = [np.hypot(self._prevCells[s_from]['xLocs'] -
                               self._currCells[strmID]['xLocs'],
                              self._prevCells[s_from]['yLocs'] -
                               self._currCells[strmID]['yLocs']) for
                     strmID in s_tos]

            strm_to = s_tos[np.argmin(dists)]

            # Ok, so *s_from* is being matched to *strm_to*
            # We want to get *strm_to* out of *strms_start*
            strms_start.pop(strm_to, None)

            # Now, remove *s_from* from *strms_end*.
            # If it wasn't in strms_end, then it was tracked...
            trckID = strms_end.pop(s_from, None)

            # We need to add *strm_to* to *strms_keep* if it isn't there already
            if strm_to not in strms_keep :
                if trckID is None :
                    raise Exception("ERROR: Unknown trckID for split!")
                # This should only happen if *s_from* was in *strms_end*
                strms_keep[strm_to] = trckID
            elif (trckID is not None) and strms_keep[strm_to] !=  trckID :
                print "WARNING! Odd splitting happened!"


    def _update_tracks(self, currStrms, currFrame,
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
            self.tracks.append(np.array([currStrms[strmID]],
                                        dtype=volume_dtype))

        # Mark any length-1 tracks for strms_end as False Alarms
        for trackID in strms_end.values() :
            if len(self.tracks[trackID]) == 1 :
                self.tracks[trackID]['types'][-1] = 'F'
            else :
                self.tracks[trackID]['types'][-1] = 'M'

    def TrackStep(self, volume_data, ellipses=None) :
        """
        Perform tracking with a new frame of data.

        *volume_data*       TODO

        *ellipses*      A list of tuples of ellipse params
                          [((h_0, k_0), a_0, b_0, t_0),
                           ((h_1, k_1), a_1, b_1, t_1),
                           ...
                          ]
                        for all current storms.
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

        self.ellipses.append([None] * len(self._currCells) 
                             if ellipses is None else
                             ellipses)

        C = self._calc_cost(self._prevCells, self._currCells)
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

        merge_into = self.find_merges(dT, strms_end, strms_keep, strms_start)
        split_from = self.find_splits(dT, strms_end, strms_keep, strms_start)
        self._handle_merges(strms_end, strms_keep, strms_start, merge_into)
        self._handle_splits(strms_end, strms_keep, strms_start, split_from)

        self._update_tracks(self._currCells, frameNum,
                            strms_end, strms_keep, strms_start)

        # The union of tracks that were kept and started for the next loop
        # iteration. This is used extensively throughout _process_assocs()
        # and finalize().
        self.prevStorms = dict(strms_keep, **strms_start)

        return strms_end, strms_keep, strms_start

    @staticmethod
    def _double_exp_smoothing(x, dT, alpha, beta) :
        """
        Provide a smoothed estimate of x[-1] based upon
        the past history of x (first values in the array
        being the earliest in history).

        Also provide the smoothed estimate of the current trend.
        """
        # Initializing smoothed data value
        s = x[0]
        # Initializing Trend estimation
        b = (x[1] - x[0]) / dT[0]

        for curIndex in range(1, len(x)) :
            F = s + b*dT[curIndex - 1]
            s_prev = s
            s = (alpha*x[curIndex] +
                 (1 - alpha)*F)
            b = (beta*((s - s_prev)/dT[curIndex-1]) +
                 (1 - beta)*b)

        return s, b

       

    def forecast_tracks(self, deltaT, trackIDs) :
        # Should probably be either properties of the object
        # or parameters into this function.
        # Current values choosen based on Dixon and Weiner paper
        frames_back = 6
        alpha = 0.5
        # F-cast parameters
        params = ['xLocs', 'yLocs', 'sizes']

        fcasts = [None] * len(trackIDs)
        trends = [None] * len(trackIDs)
        for fIndex, trackIndex in enumerate(trackIDs) :
            track = self.tracks[trackIndex]

            # Grab only the variables you want for at most the past
            # *frames_back* frames.
            x = track[params][-frames_back:]
            dT = np.diff(track['frameNums'][-frames_back:])

            trnd = np.zeros((1,), dtype=x.dtype)

            if len(track) > 1 :
                tmp = np.empty((1,), dtype=x.dtype)

                for p in params :
                    s, trnd[p] = self._double_exp_smoothing(x[p], dT, alpha, alpha)
                    tmp[p] = s + trnd[p]*deltaT
                fcasts[fIndex] = np.array(tmp[0])


            elif len(track) == 1 :
                # Do a persistence fcast
                fcasts[fIndex] = np.array(x[-1])

            trends[fIndex] = trnd

        return fcasts, trends

    def forecast_ellipses(self, deltaT, trackIDs, ellipses) :
        """
        Provided a list of ellipse tuples for each track, produce
        a list of ellipse tuples that represents the forecasted
        state of the ellipses.
        """
        # Get the f-casted positions and sizes
        fcasts, _ = self.forecast_tracks(deltaT, trackIDs)
        f_ellipses = [None] * len(ellipses)

        for index, (ellpse, f) in enumerate(zip(ellipses, fcasts)) :
            if f is None or ellpse is None :
                continue

            # Assume aspect ratio and angle remains the same
            h = np.squeeze(f['xLocs'])
            k = np.squeeze(f['yLocs'])
            szChange = np.sqrt(self.tracks[trackIDs[index]][-1]['sizes'] /
                               f['sizes'])
            a = ellpse[1] / szChange
            b = ellpse[2] / szChange
            f_ellipses[index] = ((h, k), a, b, ellpse[3])

        return f_ellipses
            

    @staticmethod
    def _contains(x, y, h, k, a, b, t) :
        """
        Determine if the ellipse described by *h*, *k*, *a*, *b*, *t*
        contains the points *x* and *y*.

        If *x* and *y* are numpy arrays, then return a numpy array of bools.
        If *x* and *y* are scalars, then return a scalar boolean.

        Note: *a* and *b* are full axes lengths, not half-lengths.
              *t* is in degrees
        """
        ox = x - h
        oy = y - k
        t = np.deg2rad(t)
        rotx = ox * np.cos(t) + oy * np.sin(t)
        roty = -ox * np.sin(t) + oy * np.cos(t)
        dist_x = rotx / (a / 2)
        dist_y = roty / (b / 2)
        return (np.hypot(dist_x, dist_y) <= 1)

    @staticmethod
    def reverse_lookup(strms_end, strms_keep, strms_start) :
        """
        Create reverse lookup dictionaries for the resulting dictionaries from
        self.TrackStep().
        """
        return ({trackID:strmID for strmID, trackID in strms_end.iteritems()},
                {trackID:strmID for strmID, trackID in strms_keep.iteritems()},
                {trackID:strmID for strmID, trackID in strms_start.iteritems()})

    def find_merges(self, deltaT, strms_end, strms_keep, strms_start,
                          frameIndex=-1) :
        """
        *deltaT*        The time difference (units of 'frameNums') between the
                        storms in *strms_end* and the storms in *strms_new*.

        *strms_end*     dict of storm indices for storms at index-1 with
                        value trackID
        *strms_keep*    dict of storm indices for storms at index with
                        value trackID
        *strms_start*   dict of storm indices for storms at index with
                        value trackID

        *frameIndex*    Index number for the frame to operate on (not fully
                        implemented!)
                        By default, operate on the most recent frame.

        Returns a dict of (strmID_1, strmID_2) pairs where strmID_2 is
        the storm index that strmID_1 was being merged into.
        If -1, then it did not merge into any other tracks
        """
        # Merge these two dictionaries into a single dict for active storms
        strms = dict(strms_keep, **strms_start)

        # strmIDs, trackIDs
        act_strms, act_ids = (((), ()) if len(strms) == 0 else
                              zip(*strms.items()))

        inact_strms, inact_ids = (((), ()) if len(strms_end) == 0 else
                                  zip(*strms_end.items()))

        fcasted_pts, _ = self.forecast_tracks(deltaT, inact_ids)
        merged_into = self._match_to_ellipses(fcasted_pts,
                            [self.ellipses[frameIndex][strmID] for strmID in
                             act_strms])

        return {strmID : (-1 if index == -1 else act_strms[index]) for
                strmID, index in zip(inact_strms, merged_into)}
        

    def find_splits(self, deltaT, strms_end, strms_keep, strms_start,
                          frameIndex=-1) :
        """
        *deltaT*        The time difference (units of 'frameNums') between the
                        storms in *strms_end* and the storms in *strms_new*.

        *strms_end*     dict of storm indices for storms at index-1 with
                        value trackID
        *strms_keep*    dict of storm indices for storms at index with
                        value trackID
        *strms_start*   dict of storm indices for storms at index with
                        value trackID

        *frameIndex*    The frame index to operate from (not fully implemented!)
                        By default, operate from the most recent frame of data.

        Returns a dict of (strmID_1, strmID_2) pairs where strmID_2 is
        the storm index strmID_1 was being split from.  If -1, then the storm
        did not split from other tracks.
        """
        # strmIDs, trackIDs
        act_strms, act_ids = (((), ()) if len(strms_keep) == 0 else
                              zip(*strms_keep.items()))

        inact_strms, inact_ids = (((), ()) if len(strms_end) == 0 else
                                  zip(*strms_end.items()))

        orph_strms, orph_ids = (((), ()) if len(strms_start) == 0 else
                                zip(*strms_start.items()))

        previous = ([] if abs(frameIndex) >= len(self.ellipses) else
                    [self.ellipses[frameIndex - 1][index] for
                     index in inact_strms])

        # If I already have these ellipses, then I don't need to
        # forecast them, now do I?  (Plus, it would be hard to correctly
        # do a forecast because the forecasting code assumes to forecast
        # from the end of the track history)
        current = [self.ellipses[frameIndex][index] for
                   index in act_strms]
        exist_strms = inact_strms + act_strms
        ellipses = (self.forecast_ellipses(deltaT, inact_ids, previous) +
                    current)

        orphan_pts = [np.array(self._currCells[index]) for index in orph_strms]
        split_from = self._match_to_ellipses(orphan_pts, ellipses)

        return {strmID : (-1 if index == -1 else exist_strms[index]) for
                strmID, index in zip(orph_strms, split_from)}

    @staticmethod
    def _match_to_ellipses(pts, ellipses) :
        """
        *pts*       The data points to use for assignment.

        *ellipses*  A list of tuples of ellipse params
                        [((h_0, k_0), a_0, b_0, t_0),
                         ((h_1, k_1), a_1, b_1, t_1),
                         ...
                        ]

        Returns a list of integers that represent the index
        of the ellipse that the track was matched against from
        the *ellipse_fcasts*.  If the integer is -1, then the
        track was not matched against any ellipses.        
        """
        dist_to_ellps = np.empty((len(pts),))
        dist_to_ellps[:] = np.inf
        matched_to = np.array([-1] * len(pts))

        if len(pts) > 0 :
            tmpy = [((np.nan, np.nan) if p is None else
                    p[['xLocs', 'yLocs']]) for
                               p in pts]
            xs, ys = np.array(zip(*tmpy))

            for trackindex, ellp in enumerate(ellipses) :
                if ellp is None :
                    continue

                in_ellipse = TITAN._contains(xs, ys, ellp[0][0], ellp[0][1],
                                             ellp[1], ellp[2], ellp[3])
                dists = np.hypot(xs - ellp[0][0],
                                 ys - ellp[0][1])

                # If this storm matches to this ellipse better than
                # previous matches, then switch it over.
                match = (dists < dist_to_ellps)
                matched_to[in_ellipse & match] = trackindex
                dist_to_ellps[in_ellipse & match] = dists[in_ellipse & match]

        return matched_to.tolist()


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
    cornerVol = ReadCorners(os.path.join(dirPath, "InputDataFile"),
                            dirPath)['volume_data']

    true_tracks, true_falarms = FilterMHTTracks(*ReadTracks(os.path.join(
                                                    dirPath, "noise_tracks")))

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
    ax.set_title("TITAN Tracks")

    ax = grid[1]
    PlotSegments(truthtable, frameLims, axis=ax)
    ax.set_title("Track Check")

    plt.show()


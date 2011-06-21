from ZigZag.TrackUtils import volume_dtype, tracking_dtype, identifier_dtype
import numpy as np
import numpy.lib.recfunctions as nprf   # for append_fields()
from scikits.learn.utils.hungarian import hungarian

class TITAN(object) :
    """
    An object for performing the tracking portion of the TITAN algorithm
    originally designed by Mike Dixon.

    This implementation is currently incomplete.  In particular, the
    volume of the stormcell is not included, even though one could set
    a weight for the volume part of the cost matrix.
    """
    def __init__(self, distWeight=1.0, volWeight=1.0, costThresh=5.0) :
        self.distWeight = distWeight
        self.volWeight = volWeight
        self.costThresh = costThresh
        self._highCost = None

        self.reinit_tracker()

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

        C = np.hypot(x0[:, np.newaxis] - x1[np.newaxis, :],
                     y0[:, np.newaxis] - y1[np.newaxis, :])

        # Make sure the highcost is gonna be high enough
        # The total cost is going to be the sum of costs over
        # the assignments.  Since there will be at most min(C.shape)
        # assignments, then multiplying the number of possible assignments
        # by the maximum assignment cost should guarantee a high enough cost.
        # Multiplying by 10 is just for extra measure.
        self._highCost = (10 * (min(C.shape) * C.max())) if C.size > 0 else 999999

        # Just double-checking that _highCost will pass the reject_assoc() later.
        if not self._reject_assoc(self._highCost) :
            # TODO: Need better safety here... I would likely prefer np.inf, maybe
            # Because that wasn't good enough to satisfy _reject_assoc(),
            #   go back to the fall-back of 999999.
            self._highCost = 999999.0

        return np.where(self._reject_assoc(C), self._highCost, C)

    def _reject_assoc(self, cost_val) :
        """ Reject this association because they were too far apart """
        return cost_val >= self.costThresh

    def _process_assocs(self, assocs, cost, currStrmCnt) :
        strms_end = {}
        strms_start = {}
        strms_keep = {}

        for t0_index, t1_index in enumerate(assocs) :
            if self._reject_assoc(cost[t0_index, t1_index]) :
                # Because of the rejection, split this
                # association into the termination of
                # one track and the start of a new track
                strms_end[t0_index] = self.prevStorms[t0_index]
                # TrackID will be assigned when the track is created
                strms_start[t1_index] = None
            else :
                strms_keep[t1_index] = self.prevStorms[t0_index]

        # Determine which other current storms were not associated
        # This happens when there are more current storms than previous storms
        newstorms = set(range(currStrmCnt)) - set(assocs)
        strms_start.update(zip(newstorms, [None]*len(newstorms)))

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
                                           ('frameNums', 'types', 'trackID'),
                                           ([currFrame] * strmCnt,
                                            ['U'] * strmCnt,
                                            [-1] * strmCnt),
                                           dtypes=[dtype[1] for dtype in
                                                   (tracking_dtype +
                                                    identifier_dtype)],
                                           usemask=False)


        for strmID, trackID in strms_keep.iteritems() :
            # A poor-man's append for numpy arrays...
            #currStrms[strmID]['types'] = 'M'
            currStrms[strmID]['trackID'] = trackID
            # Update the last storm cell listed in the track as matched
            self.tracks[trackID]['types'][-1] = 'M'
            self.tracks[trackID] = np.hstack((self.tracks[trackID], currStrms[strmID]))

        for strmID in strms_start.keys() :
            trackID = len(self.tracks)
            strms_start[strmID] = trackID
            #currStrms[strmID]['types'] = 'M'
            currStrms[strmID]['trackID'] = trackID
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
        assocs = hungarian(C)

        # Return the storms organized by their status.
        # strms_end  :  dict of storm indices for storms at index-1 with value trackID
        # strms_keep :  dict of storm indices for storms at index with value trackID
        # strms_start:  dict of storm indices for storms at index with value trackID
        strms_end, strms_keep, strms_start = self._process_assocs(assocs, C, len(currCells))

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

    t = TITAN(costThresh=5)

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


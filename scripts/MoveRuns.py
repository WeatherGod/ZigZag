#!/usr/bin/env python

from ZigZag.ListRuns import MultiSims2Sims, CommonTrackRuns,\
                            ExpandTrackRuns, RenameRuns

def main(args) :
    if args.old is None :
        parser.error("ERROR: Missing OLD")
    if args.new is None :
        parser.error("ERROR: Missing NEW")

    simNames = args.simNames if not args.isMulti else MultiSims2Sims(args.simNames, args.directory)

    trackers = CommonTrackRuns(simNames, args.directory)
    trackRuns = ExpandTrackRuns(trackers, args.trackRuns)

    # Some sanity-checking before we start
    newRuns = [aRun.replace(args.old, args.new) for aRun in trackRuns]
    if any([(oldRun == newRun) for oldRun, newRun in
            zip(trackRuns, newRuns)]) :
        raise ValueError("Some track runs do not match the pattern, or the replacement results in no change")

    # Need to see if any new names match any of those in
    # the old list, which *could* cause collisions during the
    # rename process
    if any([(oldRun == newRun) for oldRun in trackRuns
                               for newRun in newRuns]) :
        raise ValueError("This results in possible renaming collisions. Aborting...")

    # Need to make sure that the resulting names are unique
    if len(set(newRuns)) != len(newRuns) :
        raise ValueError("This results in renaming many track runs into fewer track runs.  Aborting...")

    for aSim in simNames :
        # TODO: need to do some checking work to make sure that everything
        # will either be undone on error, or that we check ahead for any
        # such possibilities.
        RenameRuns(aSim, args.old, args.new, trackRuns,
                   dirName=args.directory)


if __name__ == '__main__' :
    import argparse
    from ZigZag.zigargs import AddCommandParser


    parser = argparse.ArgumentParser(description="Rename the track runs")
    AddCommandParser('MoveRuns', parser)
    args = parser.parse_args()

    main(args)



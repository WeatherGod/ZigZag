

def SaveSimulationParams(simParamName, simParams) :
    simParamFile = open(simParamName, 'w')
    simParamFile.write("seed = %d\n" % (simParams['theSeed']))
    simParamFile.write("frameCnt = %d\n" % (simParams['frameCnt']))
    simParamFile.write("totalTracks = %d\n" % (simParams['totalTracks']))
    simParamFile.write("speed_variance = %.2f\n" % (simParams['speed_variance']))
    simParamFile.write("mean_dir = %.1f\n" % (simParams['mean_dir']))
    simParamFile.write("angle_variance = %.1f\n" % (simParams['angle_variance']))
    simParamFile.write("endTrackProb = %.5f\n" % (simParams['endTrackProb']))
    simParamFile.write("xLims = %f %f\n" % (min(simParams['xLims']), max(simParams['xLims'])))
    simParamFile.write("yLims = %f %f\n" % (min(simParams['yLims']), max(simParams['yLims'])))
    simParamFile.write("speedLims = %f %f\n" % (min(simParams['speedLims']), max(simParams['speedLims'])))

    simParamFile.write("false_merge_dist = %.2f\n" % (simParams['false_merge_dist']))
    simParamFile.write("false_merge_prob = %.5f\n" % (simParams['false_merge_prob']))

    simParamFile.write("corner_filestem = " + simParams['corner_filestem'] + "\n")
    simParamFile.write("inputDataFile = " + simParams['inputDataFile'] + "\n")
    simParamFile.write("simTrackFile = " + simParams['simTrackFile'] + "\n")
    simParamFile.write("noisyTrackFile = " + simParams['noisyTrackFile'] + "\n")
    simParamFile.write("result_filestem = " + simParams['result_filestem'] + "\n")

    simParamFile.close()

def ReadSimulationParams(simParamName) :
    simParams = {}
    for aLine in open(simParamName, 'r') :
	lineSplit = aLine.split('=')
	keyVal = lineSplit[0].strip()
	assignVal = ''.join(lineSplit[1:]).strip()

	if (keyVal == 'seed' or keyVal == 'frameCnt' or keyVal == 'totalTracks') :
	    assignVal = int(assignVal)
	elif (keyVal == 'speed_variance' or keyVal == 'mean_dir' or 
	      keyVal == 'angle_variance' or keyVal == 'endTrackProb' or
	      keyVal == 'false_merge_dist' or keyVal == 'false_merge_prob') :
	    assignVal = float(assignVal)
	elif (keyVal == 'xLims' or keyVal == 'yLims' or keyVal == 'speedLims') :
	    assignVal = map(float, assignVal.strip().split())

	simParams[keyVal] = assignVal
    
    return simParams


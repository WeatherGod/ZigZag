import os
from setuptools import setup

setup(
    name = "ZigZag",
    version = "0.8.0",
    author = "Benjamin Root",
    author_email = "ben.v.root@gmail.com",
    description = "Storm track simulator and tracker evaluator.",
    license = "BSD",
    keywords = "track simulator evalutator tracker",
    url = "https://github.com/WeatherGod/ZigZag",
    packages = ['ZigZag', 'ZigZag.Sim', 'ZigZag.Trackers'],
    package_dir = {'': 'lib'},
    scripts = ['scripts/AnalyzeTracking.py', 'scripts/DoTracking.py',
               'scripts/DownsampleSim.py', 'scripts/ListRuns.py',
               'scripts/MoveRuns.py',
               'scripts/MultiAnalysis.py', 'scripts/MultiDownsample.py',
               'scripts/MultiScenarioAnalysis.py', 'scripts/MultiSim.py',
               'scripts/MultiTracking.py', 'scripts/ParamSearch.py',
               'scripts/ShowAnims.py', 'scripts/ShowCorners.py',
               'scripts/ShowOcclusions.py', 'scripts/ShowTracks.py',
                # Temporary scripts slated to replace previous plotters
               'scripts/ShowTracks2.py', 'scripts/ShowCorners2.py', 'scripts/ShowCompare2.py',

               'scripts/TrackReports.py', 'scripts/TrackSim.py',
               'scripts/ZigZag']
    )


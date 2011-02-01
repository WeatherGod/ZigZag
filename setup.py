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
    scripts = ['AnalyzeTracking.py', 'DoTracking.py', 'DownsampleSim.py',
                'ListRuns.py', 'MultiAnalysis.py', 'MultiDownsample.py',
                'MultiScenarioAnalysis.py', 'MultiSim.py', 'MultiTracking.py',
                'ParamSearch.py', 'ShowAnims.py', 'ShowCorners.py',
                'ShowOcclusions.py', 'ShowTracks.py', 'TrackSim.py'])


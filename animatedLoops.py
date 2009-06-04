import subprocess   # for issuing commands to the OS

try:
    subprocess.call(['mogrify', '-version'])
except OSError, e:
    print "ERROR: Could not find proper install of 'mogrify':", e

try:
    subprocess.call(['convert', '-version'])
except OSError, e:
    print "ERROR: Could not find proper install of 'convert':", e


def AnimateLoop(inputFiles, outputFile):
# Probably could be doing a whole bunch of fancier checks and
# robustness like making sure that inputFiles is an array, mayber?
# Also could check the existance of the stated files, and the writability
# of the desired output file.  Maybe also make the second command not
# execute unless everything is ok with the first...
    subprocess.call(['mogrify', '-trim', '+repage'] + inputFiles)
    subprocess.call(['convert'] + inputFiles + 
    		    ['-set', 'delay', '20', '-set', 'dispose', 'none', 
		     '-loop', '0', '-layers', 'optimize', outputFile])


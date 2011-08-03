import os.path
from subprocess import call

progDir = os.path.expanduser("~/Programs/mht_tracking/tracking/")

def track(resultFile, paramFile, inputDataFile, dirName) :
    FNULL = open('/dev/null', 'w')
    retcode = call([os.path.join(progDir, 'trackCorners'),
                    '-o', resultFile,
                    '-p', paramFile,
                    '-i', inputDataFile,
                    '-d', dirName], shell=False,
                   stdout=FNULL, stderr=FNULL)
    FNULL.close()
    return retcode


def SaveMHTParams(filename, mhtParams) :
    file = open(filename, 'w')

    file.write("""; position varianceX
%(varx)f
;
; position varianceY
%(vary)f
;
; gradient variance
%(vargrad)f
;
; intensity Variance
%(varint)f
;
; process variance
%(varproc)f
;
; probability of detection
%(pod)f
;
;Lamda_x
%(lambdax)f
;
; mean new tracks per scan
%(ntps)f
;
; mean false alarms per scan
%(mfaps)f
;
; maximum number of global hypotheses per group
%(mxghpg)d
;
; maximum depth of track trees
%(mxdpth)d
;
; minimum ratio between likelihoods of worst and best
;   global hypotheses
%(mnratio)f
;
; Intensity Threshold
%(intthrsh)f
;
;
; maximum mahalanobis distance for validationi MODEL 1
5.9
;
; maximum mahalanobis distance for validationi MODEL 2 (CONSTANTVEL with z=2)
%(mxdist)f
;
; maximum mahalanobis distance for validationi MODEL 3
12.9
;
;Initial state Variance(Velocity component)
%(varvel)f
;
; number of scans to make
%(frames)d
;
; scan at which to start diagnostic A
999999
;
; scan at which to start diagnostic B
999999
;
; scan at which to start diagnostic C
999999
""" % mhtParams)

    file.close()



if __name__ == '__main__' :
    import argparse     # for command-line parsing


    parser = argparse.ArgumentParser("Create a parameter file for MHT")
    parser.add_argument("filename",
                        help="Create a parameter file called FILE",
                        metavar="FILE")


    parser.add_argument("--varx", type=float, default=1.0)
    parser.add_argument("--vary", type=float, default=1.0)
    parser.add_argument("--vargrad", type=float, default=0.01)
    parser.add_argument("--varint", type=float, default=100.0)
    parser.add_argument("--varproc", type=float, default=0.5)

    parser.add_argument("--pod", type=float, default=0.9999)
    parser.add_argument("--lambdax", type=float, default=20)
    parser.add_argument("--ntps", type=float, default=0.004)
    parser.add_argument("--mfaps", type=float, default=0.0002)
    parser.add_argument("--mxghpg", type=int, default=300)

    parser.add_argument("--mxdpth", type=int, default=3)
    parser.add_argument("--mnratio", type=float, default=0.001)
    parser.add_argument("--intthrsh", type=float, default=0.90)
    parser.add_argument("--mxdist", type=float, default=5.9)

    parser.add_argument("--varvel", type=float, default=200.0)

    parser.add_argument("--frames", type=int, default=999999)

    args = parser.parse_args()


    SaveMHTParams(args.filename, args.__dict__)


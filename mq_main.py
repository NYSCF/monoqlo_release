"""
Deep learning monoclonalization workflow v0.2.1
Author - Brodie Fischbacher
Proprietor - The New York Stem Cell Foundation
"""

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "1"

import argparse
import sys
import datetime

import processing
import mq_utils
from mq_models import load_models

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--run',
                    help="run ID if only one run is to be processed",
                    default="all")
parser.add_argument('-p', '--plate',
                    help="plate ID if only one plate is to be processed",
                    default="all")
parser.add_argument('-w', '--well',
                    help="run ID if only one run is to be processed",
                    default="all")
parser.add_argument('-c', '--cron',
                    help="is script being run from crontab - true/false",
                    default="false")
parser.add_argument('-d', '--dir',
                    help='path to directory if different from celigo exports',
                    default='ce')
parser.add_argument('-f', '--writefiles',
                    help='true/false - should output files be written to dropbox',
                    default='false')
parser.add_argument('-a', '--active',
                    help='path to file detailing active plates',
                    default="example_active_plates.txt")
args = vars(parser.parse_args())

if args["cron"] == "true":
    sys.stderr = open("Monoqlo/Logs/" +
                      str(datetime.datetime.now()) + ".err", "w")
    sys.stdout = open("Monoqlo/Logs/" +
                      str(datetime.datetime.now()) + ".log", "w")

if args["writefiles"] == "true":
    writefiles = True
else:
    writefiles = False

if args["cron"] == "true":
    crontab = True
else:
    crontab = False


dir_path = args["dir"]
active_plates_path = args["--active"]

pmodels = load_models()


##########################################################################
#
#   Customizable processing
#
##########################################################################

if args["run"] is not "all":
    print("Processing only run " + args["run"])
    plateIDs, image_list = mq_utils.enumerateRunDir(dir_path + args["run"] + "/")
    if args["plate"] is not "all":
        if args["well"] is not "all":
            processing.process_well(image_list, args["run"], args["plate"], args["well"], [], pmodels)
        else:
            processing.process_plate(image_list, args["plate"], pmodels)
    else:
        processing.process_run(dir_path + args["run"] + "/", pmodels, writefiles=writefiles)
else:
    processing.process_active_plates(dir_path, pmodels, active_plates_path, writefiles=writefiles, crontab=crontab)

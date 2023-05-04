#!/usr/bin/env python

import sys, os, stat, shutil, argparse, zipfile, time
import subprocess
import pandas as pd
import mrcfile as mrc
import numpy as np


########### USER INPUT ###########
if  __name__ == "__main__":
    parser = argparse.ArgumentParser(description='BioEM Toolkit')
    parser.add_argument('--option-file',metavar='OPTION_FILE',
                        dest='option_file',
                        help='PATH to the OPTION file',
                        required=True)
    # parser.add_argument('runmode', metavar='OPTION', nargs='+',
    #                     help='PATH to the OPTION file')
    # parser.add_argument('--option', dest='accumulate', action='store_const',
    #                     const=sum, default=max,
    #                     help='sum the integers (default: find the max)')

    args = parser.parse_args()
    option_file_path = os.path.abspath(args.option_file)

    # print(option_file_path)

option_list = []
with open(option_file_path, 'r') as opt:
    option_lines = opt.readlines()
    for line in option_lines:
        line = line.split()
        option_list = np.append(option_list,line)
        isExist = os.path.exists(line[1])
        # print(line[1],isExist)
        if isExist is False:
            print("===== %s is not existed. May cause future crash!!"%(line[1]))
        else:
            print("===== %s is checked"%(line[1]))

option_list = option_list.reshape(6,2)

class OPTION:
    def __init__(
        self, optionList
    ):

        self.optionList = optionList

    def MODEL_PATH(self):
        abs_path = os.path.abspath(self.optionList[0,1])
        return abs_path

    def MODEL_LIST_FILE_PATH(self):
        abs_path = os.path.abspath(self.optionList[1,1])
        return abs_path

    def GROUP_LIST_FILE_PATH(self):
        abs_path = os.path.abspath(self.optionList[2,1])
        return abs_path

    def LIBRARY_PATH(self):
        abs_path = os.path.abspath(self.optionList[3,1])
        return abs_path

    def PARTICLE_PATH(self):
        abs_path = os.path.abspath(self.optionList[4,1])
        return abs_path

    def OUTPUT_PATH(self):
        abs_path = os.path.abspath(self.optionList[5,1])
        return abs_path

options = OPTION(option_list)
model_path = options.MODEL_PATH()

print(model_path)

# print(options.read())


    # parser = argparse.ArgumentParser(description="""
    # """)
    # parser.add_argument("-mp", help="Absolute path to where models are stored.")
    # parser.add_argument("-ml", help="Text file with a list of all models.")
    # parser.add_argument("-gl", help="List of groups which particles are organised into. Eg. 0-10k 0-10k.mrcs 10000")
    # parser.add_argument("-param", help="Absolute path to parameters files which this script uses. Usually stored in the github repo in 'bioem_toolkit/library'.")
    # parser.add_argument("-pp", help="Absolute path of directory where particle .mrcs files are stored.")
    # parser.add_argument("-op", dest="op", help="Directory where output will be stored.")
    # parser.add_argument("--option-file","-option", dest="option_file", help="Path to OPTIONS file")
    # parser.add_argument("--run-mode","-rmod", dest="run_mode", help="Path to OPTIONS file")

    # parser.add_argument("--normal-model","-nm", dest="consensus_model", help="Name of consensus model. The model must be in the particles directory. Specify without the '.txt' extension. When this flag is used the script will run in consensus mode.")
    # parser.add_argument("--consensus-model","-cm", dest="consensus_model", help="Name of consensus model. The model must be in the particles directory. Specify without the '.txt' extension. When this flag is used the script will run in consensus mode.")
    # parser.add_argument("--make-directories","-d", dest="make_directories", action='store_true', help="When this flag is set, the script will set up the directory tree for you to run bioem. You will need to do this at least once.")
    # parser.add_argument("--round","-r ", dest="round_choice",  help="Specify which round of bioem to run. Round 1 or Round 2. 'both' is also an acceptable keyword. ", type=str)
    # parser.add_argument("-cmd", "--command_line_mode", dest = "command_line_mode",  action="store_true",  help="Choose whether to run the code in interactive mode.")
    # parser.add_argument("--submit","-s", dest = "submit",  action="store_true",  help="Submit the job scripts.")

    # print(str(option_file))
    # mp_v = args.mp
    # ml_v = args.ml
    # gl_v = args.gl
    # param_v = args.param
    # particle_v = args.pp
    # op_v = args.op

    # print("==========================")
    # print("MODEL PATH     : " + str(mp_v))
    # print("MODEL LIST     : " + str(ml_v))
    # print("DIVIDED GROUPS : " + str(gl_v))
    # print("PARAMETER PATH : " + str(param_v))
    # print("PARTICLES PATH : " + str(particle_v))
    # print("OUTPUT PATH    : " + str(op_v))
    # print("==========================")
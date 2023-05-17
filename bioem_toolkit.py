#!/usr/bin/env python

import sys, os, stat, shutil, argparse, zipfile, time
import subprocess
import pandas as pd
import mrcfile as mrc
import numpy as np
# import ray
# adding library to the system path
# from multiprocessing import Process

#TODO refactor code so that consensus is just a type of job. 
# TODO submit make orientation for consensus job. 
# TODO make grid multiplication a part of round 1. 

sys.path.insert(0, "helper_functions.py")
from helper_functions import *


#################################### NORMAL CLASSES
class NORMAL_MODE_ROUND1:
    """A simple example class"""

    def __init__(
        self, model_path, model_list, group_list, param_path, particle_path, output_path
    ):
        self.model_path = model_path
        self.model_list = model_list
        self.group_list = group_list
        self.param_path = param_path
        self.particle_path = particle_path
        self.output_path = output_path

    def PREP(self):
        global partition_choice   #### MAYBE ADD N_NODE
        partition_choice = choosing_cluster(1)
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()

        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        # print(GROUPS)
        # Strips the newline character
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                print("%s is skipped." % (MODEL[1:]))
                continue
            a_model_path = os.path.join(op_v, MODEL)
            os.makedirs(a_model_path, exist_ok="True")
            os.makedirs(os.path.join(a_model_path, "round1"), exist_ok="True")

            for ind, GROUP in GROUPS.iterrows():
                round1_path = os.path.join(a_model_path,"round1")
                r1_group_path = os.path.join(round1_path, GROUP['group'])
                os.makedirs(r1_group_path, exist_ok='True')

                shutil.copy(os.path.join(mp_v, MODEL + ".txt"), a_model_path)
                shutil.copy(param_v + "/Quat_36864", round1_path)

                with open(param_v + "/Param_BioEM_template", "r+") as file:
                    param_file = file.read()
                    param_file_out_path = str(round1_path) + "/Param_BioEM_%s"%(GROUP['group'])
                    # print(param_file_out_path)
                    param_file = param_file.replace("WhereRound1AngleFile", r1_group_path+"/angle_output_probabilities.txt")
                    with open(param_file_out_path, "w+") as outfile:
                        outfile.write(param_file)
                    os.chmod(param_file_out_path, stat.S_IRWXU)

                with open(param_v + "/slurm-r1-template.sh", "r+") as file:
                    slurm_file = file.read()
                    slurm_file_out_path = str(r1_group_path) + "/slurm-r1-rusty.sh"
                    # print(slurm_file_out_path)
                    slurm_file = slurm_file.replace("WhereSlurm", r1_group_path)
                    slurm_file = slurm_file.replace("WhatModel", MODEL)
                    slurm_file = slurm_file.replace(
                        "WhereParticle",
                        os.path.join(self.particle_path, GROUP["particle_file"]),
                    )
                    slurm_file = slurm_file.replace("WhereModel", os.path.join(self.model_path))
                    slurm_file = slurm_file.replace("WhatGroup", GROUP["group"])
                    slurm_file = slurm_file.replace("WhatPartition", partition_choice)
                    slurm_file = slurm_file.replace("WhereParam", os.path.join(round1_path,"Param_BioEM_%s"%(GROUP['group'])))
                    slurm_file = slurm_file.replace("WhereQuatern", os.path.join(round1_path,"Quat_36864") )
                    slurm_file = slurm_file.replace("WhereOutputStored", os.path.join(r1_group_path,"Output_Probabilities") )


                    with open(slurm_file_out_path, "w+") as outfile:
                        outfile.write(slurm_file)
                    os.chmod(slurm_file_out_path, stat.S_IRWXU)

    def RUN(self):
        # print('running!')
        partition_choice = choosing_cluster(1)

        centraltask_path = os.path.join(self.output_path,"0-CentralTask")
        os.makedirs(centraltask_path,exist_ok=True)
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        centraltask_filename ='CENTRAL_TASK_R1'

        with open(centraltask_path+"/CENTRAL_TASK_R1","w+") as ct:
            for MODEL in MODELS:
                MODEL = MODEL.strip()
                if MODEL[0] == "#":
                    print("%s is skipped." % (MODEL[1:]))
                    continue
                a_model_path = os.path.join(op_v, MODEL)
                round1_path = os.path.join(a_model_path, "round1")
                for ind, GROUP in GROUPS.iterrows():
                    r1_group_path = os.path.join(round1_path, GROUP["group"])
                    r1_slurm_file_path = os.path.join(r1_group_path,"slurm-r1-rusty.sh")
                    r1_slurm_file_abs = os.path.abspath(r1_slurm_file_path)
                    ct.write("%s &> REPORT_R1_%s_%s\n"%(r1_slurm_file_abs,MODEL,GROUP['group']))

        cwd = os.getcwd()
        os.chdir(centraltask_path)
        n_node = input("How many nodes to run?\n")
        sbatch_cmd = ('sbatch -n %s -c 128 -p %s -J R1 disBatch %s' % (
            n_node,
            partition_choice,
            centraltask_filename,
        )
        )
        subprocess.run(sbatch_cmd,shell=True,check=True)
        os.chdir(cwd)

                # cwd = os.getcwd()
                # os.chdir(r1_group_path)
                # slurm_file_out_path = "slurm-r1-rusty.sh"

                # os.chmod(slurm_file_out_path, stat.S_IRWXU)
                # # print(slurm_file_out_path)
                # sbatch_cmd = ('sbatch %s'%(slurm_file_out_path))
                # subprocess.run(str(sbatch_cmd), shell=True, check=True)
                # os.chdir(cwd)


class NORMAL_MODE_ROUND2:
    def __init__(
        self, model_path, model_list, group_list, param_path, particle_path, output_path
    ):
        self.model_path = model_path
        self.model_list = model_list
        self.group_list = group_list
        self.param_path = param_path
        self.particle_path = particle_path
        self.output_path = output_path

    def PREP(self):
        global cluster_choice, partition_choice
        partition_choice = choosing_cluster(0)
        if partition_choice is not None:
            n_node = input("How many nodes to run?\n")
            n_cpu = input("Number of CPUs on CLUSTER: \n")
        else:   ### LOCAL MACHINE
            n_node = "1"
            n_cpu = "32"
            
        centraltask_path = os.path.join(op_v,"1-QMTask")
        if os.path.isdir(centraltask_path) is True:
            shutil.rmtree(centraltask_path)
            
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()

        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        # print(GROUPS)
        # Strips the newline character
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                print("%s is skipped." % (MODEL[1:]))
                continue
            a_model_path = os.path.join(op_v, MODEL)
            os.makedirs(a_model_path, exist_ok="True")
            os.makedirs(os.path.join(a_model_path, "round2"), exist_ok="True")
            round1_path = os.path.join(a_model_path, "round1")

            for ind, GROUP in GROUPS.iterrows():
                round2_path = os.path.join(a_model_path, "round2")
                r1_group_path = os.path.join(round1_path, GROUP["group"])
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                os.makedirs(r2_group_path, exist_ok="True")
                # print(r2_group_path)
                subdir_list = [
                    "/parameters",
                    "/orientations",
                    "/tasks",
                    "/outputs",
                    "/tmp_files",
                ]

                for sub_dir in range(len(subdir_list)):
                    os.makedirs(r2_group_path + subdir_list[sub_dir], exist_ok="True")
                    group_param_path = os.path.join(
                        r2_group_path + subdir_list[sub_dir]
                    )

                    if os.path.basename(group_param_path) == "tmp_files":
                        shutil.copy(
                        param_v + "/Param_BioEM_template", group_param_path
                        )
                        param_bio_template_path = os.path.join(
                        group_param_path, "Param_BioEM_template"
                        )
                        shutil.copy(
                        r1_group_path + "/Output_Probabilities",
                        group_param_path + "/Output_Probabilities-R1",
                        )
                        Out_Prob_R1_path = os.path.join(
                        group_param_path, "Output_Probabilities-R1"
                        )

                        clean_R1_Probability(
                        r2_group_path, 
                        Out_Prob_R1_path, 
                        param_bio_template_path,
                        GROUP
                        )
                        print("\n========== Done with PARAMETER FILES for %s" % (MODEL))

                        r1_prob = group_param_path + "/PROB_ANGLE_R1.txt"
                        shutil.copy(
                            r1_group_path + "/angle_output_probabilities.txt",
                            r1_prob,
                        )
                        
                        making_orientations_submission (
                            libraryParmPath=self.param_path,
                            r1_foo=r1_prob,
                            model_now=MODEL,
                            group_now=GROUP['group'],
                            model_tmp_path=group_param_path,
                            model_group_path=r2_group_path,
                            partition_choice=partition_choice,
                            n_node=n_node,
                            n_cpu=n_cpu,
                            path_to_output=self.output_path,
                            startFrame=GROUP['start']
                        )

                    elif os.path.basename(group_param_path) == "tasks":
                    # if os.path.basename(group_param_path)=="tasks":   # FOR TESTING
                        shutil.copy(
                            param_v + "/launch-one-NONCONSENSUS-template.sh", group_param_path
                        )
                        launch_one_path = os.path.join(
                            group_param_path, "launch-one-NONCONSENSUS-template.sh"
                        )
                        # print(launch_one_path)
                        with open(launch_one_path, "r+") as launchIn:
                            with open(
                                group_param_path + "/launch-one.sh", "w+"
                            ) as launchOut:
                                lines = launchIn.readlines()
                                for line in lines:
                                    line = line.split()
                                    # print(line)
                                    if len(line) >= 2:
                                        if line[1] == "SLURM_JOB_NAME=WhatModel-R2":
                                            line[1] = "SLURM_JOB_NAME=%s-R2" % (MODEL)
                                        elif line[1] == "WhereRound2=WhereRound2":
                                            line[1] = "WhereRound2=%s" % (round2_path)
                                        elif line[1] == "WhereParticles=WhereParticles":
                                            line[1] = "WhereParticles=%s" % (
                                                self.particle_path
                                            )
                                        elif line[1] == "WhereModel=WhereModel":
                                            line[1] = "WhereModel=%s" % (
                                                os.path.abspath(self.model_path)
                                            )
                                    # print(*line)
                                    string = "  ".join(map(str, line))
                                    launchOut.write(string + "\n")
                                launchOut.close()
                        launchIn.close()
                        os.chmod(group_param_path + "/launch-one.sh", stat.S_IRWXU)
                        # os.remove(launch_one_path)

                        task_path = os.path.join(
                            group_param_path, "task_%s_%s" % (MODEL, GROUP["group"])
                        )

                        # print(start,end,GROUP['nframe'])
                            # print(i)
                        with open(task_path, "w+") as task:
                            for i in range(int(GROUP["start"]),int(GROUP["end"])+1):
                                # print(i)
                                launch_one_command = (
                                    "./launch-one.sh %s %s %s.txt  &>> out.log"
                                    % (i, GROUP["group"], MODEL)
                                )
                                task.write(launch_one_command + "\n")
                        print(
                            "\n========== Done with creating Task File for %s" % (MODEL)
                        )
        
        centraltask_filename = "CENTRAL_TASK_R2_QM"

        cwd = os.getcwd()
        os.chdir(centraltask_path)
        # n_core = n_node*128
        sbatch_cmd = ('sbatch -n %s -c 128 -p %s -J QM disBatch %s' % (
            n_node,
            partition_choice,
            centraltask_filename,
        )
        )
        subprocess.run(sbatch_cmd,shell=True,check=True)
        os.chdir(cwd)

    def RUN(self):
        partition_choice = choosing_cluster(0)
        try:
            subprocess.check_output(
                ["disBatch", "--help"], stderr=subprocess.STDOUT
            ).decode("utf8")
            print("\n========== disBatch is LOADED. SUBMIT JOBS NOW!\n")
        except:
            print(
                "\nYou need to load disBatch to launch ROUND 2. PROGRAM TERMINATED!!!\n"
            )
        else:
            MODELS_LIST = open(self.model_list)
            MODELS = MODELS_LIST.readlines()
            GROUPS = pd.read_csv(
                self.group_list,
                names=["particle_file", "group", "start", "end", "nframe"],
                delim_whitespace="True",
                comment="#",
            )
            for MODEL in MODELS:
                MODEL = MODEL.strip()
                if MODEL[0] == "#":
                    print("========== %s is skipped." % (MODEL[1:]))
                    continue
                a_model_path = os.path.join(op_v, MODEL)
                round2_path = os.path.join(a_model_path, "round2")
                for ind, GROUP in GROUPS.iterrows():
                    r2_group_path = os.path.join(round2_path, GROUP["group"])
                    task_path = os.path.join(r2_group_path, "tasks")
                    task_file_name = "task_%s_%s" % (MODEL, GROUP["group"])
                    task_file_path = os.path.join(task_path,task_file_name)

                    current_dir = os.getcwd()
                    # print(current_dir,task_path)
                    os.chdir(task_path)
                    # print(os.getcwd())
                    # sbatch -n 2 -c 128 -p ccm -J test disBatch CENTRAL_TASK_R1
                    n_node = input("How many nodes to run?\n")
                    sbatch_cmd = ('sbatch -n %s -c 128 -p %s -J %s disBatch %s' % (
                        n_nodes,
                        partition_choice,
                        MODEL,
                        task_file_name,
                    )
                    )
                    subprocess.run(sbatch_cmd,shell=True,check=True)
                    os.chdir(current_dir)

    def CLEAN(self):
        delete_choice = input(
            "Do you want to keep the original files? Choose (0) NO or (1) YES\n"
        )
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",
        )
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                print("%s is skipped." % (MODEL[1:]))
                continue

            a_model_path = os.path.join(op_v, MODEL)
            round2_path = os.path.join(a_model_path, "round2")
            print("\n========== Now cleaning %s" % (MODEL))
            for ind, GROUP in GROUPS.iterrows():
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                path_to_your_mess = os.path.join(r2_group_path, "outputs")
                process_output_round2(
                    delete_choice,
                    MODEL,
                    GROUP["group"],
                    path_to_your_mess,
                    GROUP["nframe"],
                    GROUP["start"],
                    GROUP["end"]
                )

    def CLEAN_PARAMS(self):
        delete_choice = input(
            "Do you want to keep the original files? Choose (0) NO or (1) YES\n"
        )
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",
        )
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                print("%s is skipped." % (MODEL[1:]))
                continue
            a_model_path = os.path.join(op_v, MODEL)
            round2_path = os.path.join(a_model_path, "round2")
            GROUP = None
            print("========== Now cleaning %s" % (MODEL))
            for ind, GROUP in GROUPS.iterrows():
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                clean_params(
                    delete_choice, MODEL, GROUP["group"], r2_group_path, GROUP["nframe"], GROUP["start"],GROUP["end"]
                )


#################################### CONSENSUS CLASSES
class CONSENSUS_MODE_ROUND_1:
    def __init__(
        self, model_path, model_list, group_list, param_path, particle_path, output_path
    ):
        self.model_path = model_path
        self.model_list = model_list
        self.group_list = group_list
        self.param_path = param_path
        self.particle_path = particle_path
        self.output_path = output_path

    def PREP(self):
        global cluster_choice, partition_choice
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str,
        )
        if args.command_line_mode==False:
            consensus_MODEL_name = input("Please provide the CONSENSUS MODEL NAME:\n")
        else:
            consensus_MODEL_name = args.consensus_model
        consensus_MODEL_path = os.path.join(self.output_path, consensus_MODEL_name)
        os.makedirs(consensus_MODEL_path, exist_ok="True")
        MODEL = consensus_MODEL_name
        print("========== CONSENSUS PATH: %s" % (consensus_MODEL_path))

        round1_path = os.path.join(consensus_MODEL_path, "round1")
        os.makedirs(round1_path, exist_ok="True")

        for ind, GROUP in GROUPS.iterrows():
            r1_group_path = os.path.join(round1_path, GROUP["group"])
            os.makedirs(r1_group_path, exist_ok="True")
            shutil.copy(os.path.join(mp_v, MODEL + ".txt"), consensus_MODEL_path)
            shutil.copy(
                param_v + "/Param_BioEM_template", round1_path + "/Param_BioEM_ABC"
            )
            shutil.copy(param_v + "/Quat_36864", round1_path)
            with open(param_v + "/slurm-r1-template.sh", "r+") as file:
                slurm_file = file.read()
                slurm_file_out_path = str(r1_group_path) + "/slurm-r1-rusty.sh"
                # print(slurm_file_out_path)
                slurm_file = slurm_file.replace("WhereSlurm", r1_group_path)
                slurm_file = slurm_file.replace("WhatModel", MODEL)
                slurm_file = slurm_file.replace(
                    "WhereParticle",
                    os.path.join(self.particle_path, GROUP["particle_file"]),
                )
                slurm_file = slurm_file.replace("WhatGroup", GROUP["group"])
                with open(slurm_file_out_path, "w+") as outfile:
                    outfile.write(slurm_file)
                outfile.close()
            file.close()
            print("PREPPING CONSENSUS DONE!")

    def RUN(self):
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        print(GROUPS)
        if args.command_line_mode==False:
            consensus_MODEL_name = input("Please provide the CONSENSUS MODEL NAME:\n")
        else:
            consensus_MODEL_name = args.consensus_model
        consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
        round1_path = os.path.join(consensus_MODEL_path, "round1")
        print("\n========== CONSENSUS PATH: %s" % (consensus_MODEL_path))
        for ind, GROUP in GROUPS.iterrows():
            current_dir = os.getcwd()
            r1_group_path = os.path.join(round1_path, GROUP["group"])
            print(current_dir)
            os.chdir(r1_group_path)
            slurm_file_out_path =  "slurm-r1-rusty.sh"
            os.chmod(slurm_file_out_path, stat.S_IRWXU)
            # print(slurm_file_out_path)
            sbatch_cmd = "sbatch " + slurm_file_out_path
            subprocess.run(str(sbatch_cmd), shell=True, check=True)
            os.chdir(current_dir)


class CONSENSUS_MODE_ROUND_2:
    def __init__(
        self, model_path, model_list, group_list, param_path, particle_path, output_path
    ):
        self.model_path = model_path
        self.model_list = model_list
        self.group_list = group_list
        self.param_path = param_path
        self.particle_path = particle_path
        self.output_path = output_path

    def PREP_NONCONSENSUS(self):
        global cluster_choice, partition_choice
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        #This is here because we did consensus in round 1 but round 2 still looks at all the models we're interested in.
        consensus_MODEL_name = input(
            "\n========== Please provide the CONSENSUS MODEL NAME:\n"
        )
        consensus_MODEL_path = os.path.join(self.output_path, consensus_MODEL_name)
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                print("\n========== Models to be skip:")
                print("%s is skipped." % (MODEL[1:]))
                continue
            elif MODEL == consensus_MODEL_name:
                continue
            # print(consensus_MODEL_path)
            a_model_path = os.path.join(op_v, MODEL)
            os.makedirs(a_model_path, exist_ok="True")
            os.makedirs(os.path.join(a_model_path, "round2"), exist_ok="True")
            round1_path = os.path.join(a_model_path, "round1")

            for ind, GROUP in GROUPS.iterrows():
                consensus_round1_path = os.path.join(consensus_MODEL_path, "round1")
                consensus_round2_path = os.path.join(consensus_MODEL_path, "round2")
                consensus_round1_group_path = os.path.join(
                    consensus_round1_path, GROUP["group"]
                )
                consensus_round2_group_path = os.path.join(
                    consensus_round2_path, GROUP["group"]
                )
                # print(consensus_round2_group_path)
                round2_path = os.path.join(a_model_path, "round2")
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                os.makedirs(r2_group_path, exist_ok="True")
                subdir_list = ["/tasks", "/outputs", "/tmp_files"]

                for sub_dir in range(len(subdir_list)):
                    os.makedirs(r2_group_path + subdir_list[sub_dir], exist_ok="True")
                    group_param_path = os.path.join(
                        r2_group_path + subdir_list[sub_dir]
                    )

                    if os.path.basename(group_param_path) == "tasks":
                        # if os.path.basename(group_param_path)=="tasks":   # FOR TESTING
                        launch_one_template_path = os.path.join(
                            self.param_path, "launch-one-NONCONSENSUS-template.sh"
                        )
                        shutil.copy(launch_one_template_path, group_param_path)
                        launch_one_path = os.path.join(
                            group_param_path, "launch-one-NONCONSENSUS-template.sh"
                        )
                        # print(launch_one_path)
                        with open(launch_one_path, "r+") as launchIn:
                            with open(
                                group_param_path + "/launch-one.sh", "w+"
                            ) as launchOut:
                                lines = launchIn.readlines()
                                for line in lines:
                                    line = line.split()
                                    # print(line)
                                    if len(line) >= 2:
                                        if line[1] == "SLURM_JOB_NAME=WhatModel-R2":
                                            line[1] = "SLURM_JOB_NAME=%s-R2" % (MODEL)
                                        elif line[1] == "WhereRound2CM=WhereRound2CM":
                                            # print(consensus_round2_group_path)
                                            line[1] = "WhereRound2CM=%s" % (
                                                consensus_round2_path
                                            )
                                        elif line[1] == "WhereParticles=WhereParticles":
                                            line[1] = "WhereParticles=%s" % (
                                                self.particle_path
                                            )
                                        elif line[1] == "WhereModel=WhereModel":
                                            line[1] = "WhereModel=%s" % (
                                                os.path.abspath(self.model_path)
                                            )
                                        elif line[1] == "WhereOutput=WhereOutput":
                                            line[1] = "WhereOutput=%s" % (round2_path)
                                        elif line[1] == "WhereRound1_CONSENSUS_Results=WhereRound1_CONSENSUS_Results":
                                            # this is a place holder, beacuse we need to run the make ori script on consensus round 2 to produce the finer grid. 
                                            # really we should figure out how to make this a variable. 
                                            consensus_round2_orientations_processed =(os.path.abspath(os.path.join(consensus_round1_group_path,'../../round2/')))
                                            consensus_round2_orientations_processed = consensus_round2_orientations_processed + '/$2'
                                            line[1] = "WhereRound1_CONSENSUS_Results=%s" % (consensus_round2_orientations_processed)
                                            # print(round2_path)
                                    # print(*line)
                                    string = "  ".join(map(str, line))
                                    launchOut.write(string + "\n")
                                launchOut.close()
                        launchIn.close()
                        os.chmod(group_param_path + "/launch-one.sh", stat.S_IRWXU)
                        # os.remove(launch_one_path)

                        task_path = os.path.join(
                            group_param_path, "task_%s_%s" % (MODEL, GROUP["group"])
                        )
                        particle_count = int(GROUP["nframe"])
                        with open(task_path, "w+") as task:
                            for i in range(particle_count):
                                # print(i)
                                launch_one_command = (
                                    "./launch-one.sh %s %s %s  &>> out.log"
                                    % (i, GROUP["group"], MODEL)
                                )
                                task.write(launch_one_command + "\n")
                        task.close()
                        print(
                            "\n========== Done with TASK FILES for NON-CONSENSUS %s"
                            % (MODEL)
                        )
        print("\n========== CONSENSUS PATH: %s" % (consensus_MODEL_path))

    def PREP_CONSENSUS(self):
        global cluster_choice, partition_choice
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        if args.command_line_mode == False:
            consensus_MODEL_name = input(
                "\n========== Please provide the CONSENSUS MODEL NAME:\n"
            )
        else:
            consensus_MODEL_name = args.consensus_model
        consensus_MODEL_path = os.path.join(self.output_path, consensus_MODEL_name)
        os.makedirs(consensus_MODEL_path, exist_ok="True")
        os.makedirs(os.path.join(consensus_MODEL_path, "round2"), exist_ok="True")
        consensus_round1_path = os.path.join(consensus_MODEL_path, "round1")
        consensus_round2_path = os.path.join(consensus_MODEL_path, "round2")

        for ind, GROUP in GROUPS.iterrows():
            consensus_round1_group_path = os.path.join(
                consensus_round1_path, GROUP["group"]
            )
            consensus_round2_group_path = os.path.join(
                consensus_round2_path, GROUP["group"]
            )
            # print(consensus_round2_group_path)

            os.makedirs(consensus_round2_group_path, exist_ok="True")
            subdir_list = [
                "/parameters",
                "/orientations",
                "/tasks",
                "/outputs",
                "/tmp_files",
            ]

            for sub_dir in range(len(subdir_list)):
                os.makedirs(
                    consensus_round2_group_path + subdir_list[sub_dir], exist_ok="True"
                )

                group_param_path = os.path.join(
                    consensus_round2_group_path + subdir_list[sub_dir]
                )

                if os.path.basename(group_param_path) == "tmp_files":
                    # self.param_path+"Param_BioEM_template"
                    param_bio_R1_path = os.path.join(
                        consensus_round1_path, "Param_BioEM_ABC"
                    )
                    shutil.copy(param_bio_R1_path, group_param_path)
                    output_prob_from_R1 = os.path.join(
                        consensus_round1_group_path, "Output_Probabilities"
                    )
                    Out_copied_Prob_R1_path = os.path.join(
                        group_param_path, "Output_Probabilities-R1"
                    )
                    shutil.copy(output_prob_from_R1, Out_copied_Prob_R1_path)
                    clean_R1_Probability(
                        consensus_round2_group_path,
                        Out_copied_Prob_R1_path,
                        param_bio_R1_path,
                    )
                    print(
                        "\n========== Done with PARAMETER FILES for %s"
                        % (consensus_MODEL_name)
                    )
                    shutil.copy(
                        consensus_round1_group_path + "/angle_output_probabilities.txt",
                        group_param_path + "/PROB_ANGLE_R1.txt",
                    )
                    r1_prob = group_param_path + "/PROB_ANGLE_R1.txt"
                    a_model_path = os.path.join(op_v, consensus_MODEL_name)
                    r2_group_path = a_model_path + '/round2'
                    print(consensus_round2_group_path)
                    making_orientations_submission (libraryPath = param_v, r1_prob = r1_prob, model_now = a_model_path , group_now = consensus_round2_group_path, workdir_round2 = r2_group_path )

                    print(
                        "\n========== Done with ORIENTATION FILES for %s"
                        % (consensus_MODEL_name)
                    )

                elif os.path.basename(group_param_path) == "tasks":
                    # if os.path.basename(group_param_path)=="tasks":   # FOR TESTING
                    launch_one_template_path = os.path.join(
                        self.param_path, "launch-one-template.sh"
                    )
                    shutil.copy(launch_one_template_path, group_param_path)
                    launch_one_path = os.path.join(
                        group_param_path, "launch-one-template.sh"
                    )
                    # print(launch_one_path)
                    with open(launch_one_path, "r+") as launchIn:
                        with open(
                            group_param_path + "/launch-one.sh", "w+"
                        ) as launchOut:
                            lines = launchIn.readlines()
                            for line in lines:
                                line = line.split()
                                # print(line)
                                if len(line) >= 2:
                                    if line[1] == "SLURM_JOB_NAME=WhatModel-R2":
                                        line[1] = "SLURM_JOB_NAME=%s-R2" % (
                                            consensus_MODEL_name
                                        )
                                    elif line[1] == "WhereRound2=WhereRound2":
                                        # print(consensus_round2_group_path)
                                        line[1] = "WhereRound2=%s" % (
                                            consensus_round2_path
                                        )
                                    elif line[1] == "WhereParticles=WhereParticles":
                                        line[1] = "WhereParticles=%s" % (
                                            self.particle_path
                                        )
                                    elif line[1] == "WhereModel=WhereModel":
                                        line[1] = "WhereModel=%s" % (
                                            os.path.abspath(self.model_path)
                                        )
                                    elif line[1] == "WhereRound1_CONENSUS_Results=WhereRound1_CONENSUS_Results":
                                        print(os.path.abspath(group_param_path))
                                        line[1] = "WhereRound1_CONENSUS_Results=%s" % (
                                            os.path.abspath(group_param_path)
                                        )
                                # print(*line)
                                string = "  ".join(map(str, line))
                                launchOut.write(string + "\n")
                            launchOut.close()
                    launchIn.close()
                    os.chmod(group_param_path + "/launch-one.sh", stat.S_IRWXU)
                    # os.remove(launch_one_path)
                    task_path = os.path.join(
                        group_param_path,
                        "task_%s_%s" % (consensus_MODEL_name, GROUP["group"]),
                    )
                    particle_count = int(GROUP["nframe"])
                    with open(task_path, "w+") as task:
                        for i in range(particle_count):
                            # print(i)
                            launch_one_command = (
                                "./launch-one.sh %s %s %s  &>> out.log"
                                % (i, GROUP["group"], consensus_MODEL_name)
                            )
                            task.write(launch_one_command + "\n")
                    task.close()
                    print(
                        "\n========== Done with TASK FILES for CONSENSUS MODEL: %s"
                        % (consensus_MODEL_name)
                    )
        # print("\n========== CONSENSUS PATH: %s"%(consensus_MODEL_path))

    def RUN_NONCONSENSUS(self):
        try:
            subprocess.check_output(
                ["disBatch", "--help"], stderr=subprocess.STDOUT
            ).decode("utf8")
            print("========== disBatch is LOADED. SUBMIT JOBS NOW!")
        except:
            print(
                "\nYou need to load disBatch to launch ROUND 2. PROGRAM TERMINATED!!!\n"
            )
            exit

        consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
        consensus_MODEL_path = os.path.join(self.output_path, consensus_MODEL_name)
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                # print("%s is skipped."%(MODEL[1:]))
                continue
            elif MODEL == consensus_MODEL_name:
                continue
            a_model_path = os.path.join(op_v, MODEL)
            round2_path = os.path.join(a_model_path, "round2")
            GROUP = None
            for ind, GROUP in GROUPS.iterrows():
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                task_path = os.path.join(r2_group_path, "tasks")
                task_file_name = "task_%s_%s" % (MODEL, GROUP["group"])
                current_directory = os.getcwd()
                os.chdir(task_path)

                sbatch_cmd = "sbatch -p ccb -J %s -t 128 disBatch %s" % (
                    MODEL,
                    task_file_name,
                )
                # print(sbatch_cmd)
                subprocess.run(sbatch_cmd, shell=True)
                os.chdir(current_directory)

    def RUN_CONSENSUS(self):
        try:
            subprocess.check_output(
                ["disBatch", "--help"], stderr=subprocess.STDOUT
            ).decode("utf8")
            print("========== disBatch is LOADED. SUBMIT JOBS NOW!")
        except:
            print(
                "\nYou need to load disBatch to launch ROUND 2. PROGRAM TERMINATED!!!\n"
            )
            exit

        if args.command_line_mode == False:
            consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
        elif args.consensus_model is not None:
            consensus_MODEL_name = args.consensus_model 
        else:
            raise Exception ("It looks like you haven't specified a consensus model file but you've asked to run in consensus mode. ")
        consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        round2_path = os.path.join(consensus_MODEL_path,"round2")
        GROUP=None
        for ind, GROUP in GROUPS.iterrows():
            r2_group_path = os.path.join(round2_path, GROUP["group"])
            task_path = os.path.join(r2_group_path, "tasks")
            task_file_name = "task_%s_%s" % (consensus_MODEL_name, GROUP["group"])
            os.chdir(task_path)
            sbatch_cmd = "sbatch -p ccb -J %s -t 128 disBatch %s" % (
                consensus_MODEL_name,
                task_file_name,
            )
            # print(sbatch_cmd)
            subprocess.run(sbatch_cmd, shell=True)

    def CLEAN_OUTPUT_NONCONSENSUS(self):
        consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
        consensus_MODEL_path = os.path.join(self.output_path, consensus_MODEL_name)
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                # print("%s is skipped."%(MODEL[1:]))
                continue
            elif MODEL == consensus_MODEL_name:
                continue
            a_model_path = os.path.join(op_v, MODEL)
            round2_path = os.path.join(a_model_path, "round2")
            GROUP = None
            print("========== Now cleaning %s" % (MODEL))
            for ind, GROUP in GROUPS.iterrows():
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                path_to_your_mess = os.path.join(r2_group_path, "outputs")
                process_output_round2(
                    MODEL, GROUP["group"], path_to_your_mess, int(GROUP["nframe"])
                )

    def CLEAN_OUTPUT_CONSENSUS(self):
        consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
        consensus_MODEL_path = os.path.join(self.output_path, consensus_MODEL_name)
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        round2_path = os.path.join(consensus_MODEL_path, "round2")
        GROUP = None
        print("========== Now cleaning CONSENSUS MODEL %s" % (consensus_MODEL_name))
        for ind, GROUP in GROUPS.iterrows():
            r2_group_path = os.path.join(round2_path, GROUP["group"])
            path_to_your_mess = os.path.join(r2_group_path, "outputs")
            process_output_round2(
                consensus_MODEL_name, GROUP["group"], path_to_your_mess, int(GROUP["nframe"])
            )

    def CLEAN_PARAMS(self):
        delete_choice = input(
            "Do you want to keep the original files? Choose (0) NO or (1) YES\n"
        )
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                # print("%s is skipped."%(MODEL[1:]))
                continue
            a_model_path = os.path.join(self.output_path, MODEL)
            round2_path = os.path.join(a_model_path, "round2")
            GROUP = None
            print("========== Now cleaning PARAMETERS for MODEL %s" % (MODEL))
            for ind, GROUP in GROUPS.iterrows():
                r2_group_path = os.path.join(round2_path, GROUP["group"])
                clean_params(
                    delete_choice, MODEL, GROUP["group"], r2_group_path, int(GROUP["nframe"])
                )


########### ANALYSIS SUIT ##########
class ANALYSIS_SUIT:
    def __init__(
        self, model_path, model_list, group_list, param_path, particle_path, output_path
    ):
        self.model_path = model_path
        self.model_list = model_list
        self.group_list = group_list
        self.param_path = param_path
        self.particle_path = particle_path
        self.output_path = output_path

    # @timer_func
    def collect_r2_output(self):
        collected_r2_path = os.path.join(self.output_path, "0-COLLECTED_R2_OUTPUTS")
        MODELS_LIST = open(self.model_list)
        MODELS = MODELS_LIST.readlines()
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",
            comment="#",dtype=str
        )
        matrix_model = pd.DataFrame(dtype=float)
        for MODEL in MODELS:
            MODEL = MODEL.strip()
            if MODEL[0] == "#":
                print("%s is skipped.\n" % (MODEL[1:]))
                continue
            a_model_path = os.path.join(self.output_path, MODEL)
            for ind, GROUP in GROUPS.iterrows():
                sorted_output_file_path = os.path.join(
                    a_model_path,
                    "round2",
                    GROUP["group"],
                    "outputs",
                    "OutPut_SORTED_%s-%s" % (MODEL, GROUP["group"]),
                )
                # print(sorted_output_file_path)
                os.makedirs(collected_r2_path, exist_ok="True")
                shutil.copy(sorted_output_file_path, collected_r2_path)
        print("\n========== ALL R2 OUTPUTS COLLECTED!")

    # @timer_func
    def make_matrix_log(self):

        ### TEST BLOCK ###
        # test_path='/mnt/ceph/users/ptang/6-ABC-Transporter/1-PROCESSING/trial2/Nano_Disk_NB_Parameters.txt'
        # test_choice='ICangle'
        # cv_profile_path = test_path
        # cv_choice = test_choice
        # df_cv_profile=pd.read_csv(cv_profile_path,header=0,delim_whitespace=True,comment='#')

        cv_profile_path = input(
            "Please provide the path to your CV profile (etc. MODEL CV_1 ... CV_n)\nThe first line will be read as headers\n"
        )
        df_cv_profile = pd.read_csv(
            cv_profile_path, header=0, delim_whitespace=True, comment="#",dtype=str
        )
        cv_choice = input(
            "\n==========Your available Collective Variables (CV):\n%s\n\nPlease select the CV that you want to be SORTED:\n"
            % (df_cv_profile.columns.to_list())
        )
        df_cv_profile_sorted = df_cv_profile.sort_values(
            by=[cv_choice], ignore_index=True
        )
        df_cv_profile_sorted = df_cv_profile_sorted.rename(
            columns={df_cv_profile_sorted.columns[0]: "model"}
        )
        col = df_cv_profile_sorted.pop(cv_choice)
        df_cv_profile_sorted.insert(1, col.name, col)
        # print(df_cv_profile)
        # print(df_cv_profile_sorted)
        collected_r2_path = os.path.join(self.output_path, "0-COLLECTED_R2_OUTPUTS")
        df_cv_profile_sorted.to_csv(
            collected_r2_path + "/SORTED_ON_%s" % (cv_choice), sep="\t"
        )
        GROUPS = pd.read_csv(
            self.group_list,
            names=["particle_file", "group", "start", "end", "nframe"],
            delim_whitespace="True",dtype=str,
            comment="#",
        )
        matrix_model = pd.DataFrame()
        for idx, MODEL in df_cv_profile_sorted.iterrows():
            for ind, GROUP in GROUPS.iterrows():
                # print(GROUP)
                matrix_element = []
                copied_output_path = os.path.join(
                    collected_r2_path,
                    "OutPut_SORTED_%s-%s" % (MODEL["model"], GROUP["group"]),
                )
                with open(copied_output_path, "r+") as ofn:
                    lines = ofn.readlines()
                    for line in lines:
                        line = line.split()
                        matrix_element.append(line[3])
                matrix_model[MODEL["model"]] = matrix_element
                # print(matrix_model.head(5))

        matrix_model = matrix_model.astype(
            float
        )  # CHANGE OF TYPE MUST BE PRIOR TO ANY FUNCTION
        max_element_row = matrix_model.max(axis=1)
        matrix_model_sub = matrix_model.sub(max_element_row, axis="index")
        matrix_model_norm = matrix_model_sub.apply(lambda x: np.exp(x))

        bife_output_filename = os.path.join(collected_r2_path, "PMat")
        matrix_model_norm.to_csv(
            bife_output_filename + "-annotated", sep="\t", float_format="%1.6f"
        )
        matrix_model_norm.to_csv(
            bife_output_filename,
            sep="\t",
            float_format="%1.6f",
            header=None,
            index=False,
        )

        print(
            "\n========== The CV profile is SORTED on %s and PMAT is generated!"
            % (cv_choice)
        )

    # @timer_func
    def execute_cryoBIFE(self):
        import cmdstanpy
        from cmdstanpy import CmdStanModel

        bife_workdir_path = os.path.join(self.output_path, "1-cryoBIFE_OUTPUTS")
        os.makedirs(bife_workdir_path, exist_ok=True)

        collected_r2_path = os.path.join(self.output_path, "0-COLLECTED_R2_OUTPUTS")
        PMat_path = os.path.join(collected_r2_path, "PMat")
        my_stanfile = os.path.join(self.param_path, "cryo-bife.stan")

        my_model = CmdStanModel(stan_file=my_stanfile)
        Pmat = np.loadtxt(PMat_path)
        cryobife_data = {"M": Pmat.shape[1], "N": Pmat.shape[0], "Pmat": Pmat}
        # run CmdStan's sample method, returns object `CmdStanMCMC`
        fit = my_model.sample(data=cryobife_data)
        cryoBIFE_output_filename = os.path.join(bife_workdir_path, "STAN_result")
        u = fit.summary()
        bife_output_filename = os.path.join(
            bife_workdir_path, "cryoBIFE_%s.out" % (CVchoice)
        )
        u.to_csv(bife_output_filename, sep="\t", float_format="%1.6f")


########### INSTRUCTIONS ###########

note0 = """
##########################################################
CHOOSE THE MODE:
!!!!! WARNING !!!!!
PLEASE DOUBLE CHECK "Param_BioEM_template" BEFORE
GOING BEYOND THIS POINT 
----------------------------------------------------------

    1. NORMAL MODE
    2. CONSENSUS MODE
    3. ANALYSIS
    4. EXIT NOW
----------------------------------------------------------
##########################################################
"""

note1_normal = """
#######################################################
THIS PROGRAM IS FOR RUNNING ROUND 1                   |
-------------------------------------------------------
Select the number to run:

    1. Preparation directories
    2. Submit JOBs
    3. Exit
-------------------------------------------------------
#######################################################
"""
note1_consensus = """
#######################################################
THIS PROGRAM IS FOR ROUND 1 IN CONSENSUS MODE         |
-------------------------------------------------------
Select the number to run:

    1. Preparation directories
    2. Submit JOBs
    3. Exit
-------------------------------------------------------
#######################################################
"""

note2_consensus = """
#######################################################
THIS PROGRAM IS FOR ROUND 2 IN CONSENSUS MODE         |
-------------------------------------------------------
Select the number to run:

    1. Preparation directories
    2. Submit JOBs
    3. Post-process output
    4. Cleanup PARAMETERS
    5. Exit
-------------------------------------------------------
#######################################################
"""

note2_nonconsensus = """
#######################################################
N CONSENSUS MODE
THIS PROGRAM IS FOR ROUND 2 OF NON-CONSENSUS MODELS   |
IN CONSENSUS MODE                                     |
-------------------------------------------------------
Select the number to run:

    1. Preparation directories
    2. Submit JOBs
    3. Post-process output
    4. Cleanup PARAMETERS
    5. Exit
-------------------------------------------------------
#######################################################
"""

note2_normal = """
#######################################################
THIS PROGRAM IS FOR ROUND 2                           |
-------------------------------------------------------
Select the number to run:

    1. Preparation directories
    2. Submit JOBs
    3. Post-process output
    4. Cleanup PARAMETERS
    5. Exit
-------------------------------------------------------
#######################################################
"""

note3 = """
#######################################################
THIS PROGRAM IS FOR ROUND 2 IN CONSENSUS MODE         |
-------------------------------------------------------
Select the number to run:

    1. Preparation directories
    2. Submit JOBs
    3. Post-process output
    4. Cleanup PARAMETERS
    5. Exit
-------------------------------------------------------
#######################################################
"""

note4a = """
#######################################################
RUNNING cryoBIFE toolkits                              |
-------------------------------------------------------
Select the number to run:

    1. Preparation INPUTs
    2. Make LOG matrix
    3. Run cryo-BIFE
    4. Cleanup PARAMETERS
    5. Exit
-------------------------------------------------------
#######################################################
"""
########### USER INPUT ###########
if  __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
    # """)
    parser.add_argument("-mp", help="Absolute path to where models are stored.")
    parser.add_argument("-ml", help="Text file with a list of all models.")
    parser.add_argument("-gl", help="List of groups which particles are organised into. Eg. 0-10k 0-10k.mrcs 10000")
    parser.add_argument("-param", help="Absolute path to parameters files which this script uses. Usually stored in the github repo in 'bioem_toolkit/library'.")
    parser.add_argument("-pp", help="Absolute path of directory where particle .mrcs files are stored.")
    parser.add_argument("-op", dest="op", help="Directory where output will be stored.")
    parser.add_argument("--consensus-model",'-c', dest='consensus_model', help="Name of consensus model. The model must be in the particles directory. Specify without the '.txt' extension. When this flag is used the script will run in consensus mode.")
    parser.add_argument("-d",'--make-directories', dest='make_directories', action='store_true', help="When this flag is set, the script will set up the directory tree for you to run bioem. You will need to do this at least once.")
    parser.add_argument("-r ", "--round", dest="round_choice",  help="Specify which round of bioem to run. Round 1 or Round 2. 'both' is also an acceptable keyword. ", type=str)
    parser.add_argument("-cmd", "--command_line_mode", dest = "command_line_mode",  action="store_true",  help="Choose whether to run the code in interactive mode.")
    parser.add_argument("-s", "--submit", dest = "submit",  action="store_true",  help="Submit the job scripts.")

    args = parser.parse_args()

    mp_v = args.mp
    ml_v = args.ml
    gl_v = args.gl
    param_v = args.param
    particle_v = args.pp
    op_v = args.op

    print("==========================")
    print("MODEL PATH : " + str(mp_v))
    print("MODEL LIST     : " + str(ml_v))
    print("DIVIDED GROUPS : " + str(gl_v))
    print("PARAMETER PATH : " + str(param_v))
    print("PARTICLES PATH : " + str(particle_v))
    print("OUTPUT PATH    : " + str(op_v))
    print("==========================")

#### TESTING ####
####
#phu the logic of this is so confusing. we need to rewrite it.
final_choice = 0
while final_choice <5:
    if args.command_line_mode == False:
        mode_choice = input(note0 + "\n")
    else: 
        if args.consensus_model is not None:
            mode_choice = '2'    
            final_choice = 5
        if args.consensus_model is None:
            mode_choice = '1'
            final_choice = 5
        
    if mode_choice =='1':
        print("========== YOU CHOSE NORMAL MODE!!\n")
        job1 = NORMAL_MODE_ROUND1(mp_v, ml_v, gl_v, param_v, particle_v, op_v)
        job2 = NORMAL_MODE_ROUND2(mp_v, ml_v, gl_v, param_v, particle_v, op_v)

        if args.command_line_mode == False:
            choose_round = input("Please choose the ROUND (1 or 2):\n")
        else:
            choose_round = str(args.round_choice )
        if choose_round == "1":
            if args.command_line_mode == False:
                options = input(note1_normal + "\n")
            else: 
                if args.make_directories == True:
                    options = "1"
                elif args.submit == True:
                    options = "2"
                else: 
                    options = "3"
            if options == "1":
                model = job1.PREP()
                if args.submit == True and args.command_line_mode == True :
                    job1.RUN()

            elif options == "2":
                job1.RUN()
            elif options == "3":
                final_choice = 5
                print("Program exited.")
        else:
            if args.command_line_mode == False:
                options = input(note2_normal + "\n")
            else:
                if args.make_directories == True:
                    options = "1"
                elif args.submit == True:
                    options = "2"
                else:
                    options = "5"
            if options == "1":
                print("\nPREPPING for ROUND2.\n")
                job2.PREP()
                if args.submit == True and args.command_line_mode == True:
                    job2.RUN()
            elif options == "2":
                print("\nBATCH submission for ROUND2.\n")
                job2.RUN()
            elif options == "3":
                print("\nPOST-PROCESSING OUTPUTS!!\n")
                MODEL_PROCESSED = job2.CLEAN()
                # print("\n%s is CLEANED.\n" % (MODEL_PROCESSED))
            elif options == "4":
                print("\nCLEANING UP DIRECTORIES!\n")
                MODEL_PROCESSED = job2.CLEAN_PARAMS()
                # print("\n%s is CLEANED.\n" % (MODEL_PROCESSED))
            elif options == "5":
                final_choice = 5
                print("Program exited.")

    elif mode_choice == "2":
        print("========== YOU CHOSE CONSENSUS MODE!!\n")
        job1 = CONSENSUS_MODE_ROUND_1(mp_v, ml_v, gl_v, param_v, particle_v, op_v)
        job2 = CONSENSUS_MODE_ROUND_2(mp_v, ml_v, gl_v, param_v, particle_v, op_v)
        if args.command_line_mode == False:
            create_consensus_directories = input("Do you want to create CONSENSUS directory? (0: No, 1:Yes)?\n")
        else:
            if args.make_directories is not None:
                create_consensus_directories = str(args.make_directories)

        if create_consensus_directories == "0":
            print("========== ONLY RUN ROUND 2 for non-CONSENSUS MODELS")
            options = input(note2_nonconsensus + "\n")
            if options == "1":
                print("\nPREPPING for ROUND2.\n")
                job2.PREP_NONCONSENSUS()
            elif options == "2":
                print("\nBATCH submission for ROUND2.\n")
                job2.RUN_NONCONSENSUS()
            elif options == "3":
                print("\nPOST-PROCESSING OUTPUTS!\n")
                job2.CLEAN_OUTPUT_NONCONSENSUS()
            elif options == "4":
                job2.CLEAN_PARAMS()
            elif options == "5":
                final_choice = 5
                print("Program exited.")
        else:
            #if the -cmd or --command_line_mode mode flags are specified, we skip doing things with interactive inputs.

            #if the flag isn't set, this if statement will be run, prompting the user for inputs.
            if args.command_line_mode == False:
                print("========== MAKING CONSENSUS DIRECTORY!")
                choose_round = input("Please choose the ROUND (1) or (2) or (3) for both rounds:\n")
            else:
                if args.round_choice == False and args.command_line_mode == True :
                    raise UserWarning("It looks like you haven't specified which round of bioEM you want to run. Please specify 1, 2 or 'both' with the -r flag.")
                if args.round_choice == 'both':
                    choose_round = str(3)
                elif args.round_choice == '1' or args.round_choice == '2':
                    choose_round = str(args.round_choice)
                else:
                    raise UserWarning ("In command line mode, you have to specify which round of bioEM to run with the '-r' flag. Choices are to run round 1, round 2, or to run both rounds with the 'both' keyword.")

            if choose_round =='1':
                if args.command_line_mode==False:
                    options = input(note1_consensus+"\n")
                else:
                    if args.make_directories == True:
                        print ('Preparing CONSENSUS directory files.')
                        options = '1'
                    elif args.submit == True: 
                        print('Submitting batch job for Round 1 in Consensus Mode!')
                        options = '2'
                    else:
                        options = '3'

                print('checking')
                if options =='1':
                    print('prepping.')
                    job1.PREP()
                    #have to add this here so that we try to submit if the submit flag is there
                    if args.command_line_mode == True and args.submit == True:
                        print('Submitting batch job for Round 1 in Consensus Mode!')
                        job1.RUN()
                if options =='2':
                    job1.RUN()
                elif options=='3':
                    print("Round 1 specified, but you haven't chosen to prepare the directory tree or submit the jobs. For now the program will just exit.")
                    final_choice=5
            elif choose_round=='2':
                if args.command_line_mode==False:
                    options=input(note2_consensus+"\n")

                else:
                    if args.make_directories == True:
                        print ('Preparing directory structure for CONSENSUS MODE.')
                        options = '1'
                    elif args.submit == True: 
                        print('Submitting ROUND 2 batch jobs in CONSENSUS MODE!!')
                        options = '2'
                    else:
                        options = '3'
                if options=="1":
                    print("\nPrepping Directories Round 2 for CONSENSUS MODE.\n")
                    job2.PREP_CONSENSUS()
                    if args.command_line_mode==True and args.submit == True :
                        job2.RUN_CONSENSUS()

                elif options=="2":
                    print("\nBATCH submission in CONSENSUS MODE.\n")
                    job2.RUN_CONSENSUS()
                elif options == "3":
                    print("\nPOST-PROCESSING OUTPUTS!\n")
                    job2.CLEAN_OUTPUT_CONSENSUS()
                elif options == "4":
                    job2.CLEAN_PARAMS()
                elif options == "5":
                    final_choice = 5
                    print("Program exited.")
            elif choose_round == "3":
                options = input(note3 + "\n")
                if options == "1":
                    print("\n========== PREPPING for CONSENSUS ROUND 1 & 2.\n")
                    job1.PREP_NONCONSENSUS()
                    job2.PREP_CONSENSUS()
                elif options == "2":
                    print("\n========== BATCH submission for CONSENSUS ROUND 1 & 2.\n")
                    job1.RUN_NONCONSENSUS()
                    job2.RUN_CONSENSUS()
                elif options == "3":
                    print("\n========== POST-PROCESSING OUTPUTS!\n")
                    job1.CLEAN_OUTPUT_NONCONSENSUS()
                    job2.CLEAN_OUTPUT_CONSENSUS()
                elif options == "4":
                    print("\n========== CLEANING UP YOUR MESS NOW!\n")
                    job1.CLEAN_PARAMS()
                    job2.CLEAN_PARAMS()
                elif options == "5":
                    print("Program exited.")
                    final_choice = 5

    elif mode_choice == "3":
        print("========== ANALYSIS MODE!")
        job1 = ANALYSIS_SUIT(mp_v, ml_v, gl_v, param_v, particle_v, op_v)
        print(op_v)
        options = input(note4a + "\n")
        if options == "1":
            job1.collect_r2_output()
        elif options == "2":
            job1.make_matrix_log()
        elif options == "3":
            job1.execute_cryoBIFE()
        else:
            final_choice = 5

    elif mode_choice == "4":
        final_choice = 5

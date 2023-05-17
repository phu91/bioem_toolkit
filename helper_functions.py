#phu put the functions here. 
import sys, os, stat, shutil, argparse, zipfile, time
import subprocess
import pandas as pd
import mrcfile as mrc
import numpy as np
# import ray

def timer_func(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time()
        result = func(*args, **kwargs)
        t2 = time()
        print(f"========== Function {func.__name__!r} executed in {(t2-t1):.4f}s")
        return result

    return wrap_func

def choosing_cluster(prechoice):
    if prechoice== 0:
        cluster_choice = input("Do you want to work on CLUSTER? Yes (1) or No (0): \n")
        if cluster_choice == "1":
            partition_choice = input("Please select your PARTITION on SLURM: \n")
            return partition_choice
        else:
            print("\n========== MULTIPLY_QUAT will be done on local machine")
            return None
    elif prechoice==1:
        partition_choice = input("Please select your PARTITION on SLURM: \n")
        return partition_choice

def counter(baseZero,count):
    return int(baseZero) + count

def clean_R1_Probability(working_dir, r1_output: str, bioEM_template,group_now):
    r1_read = open(r1_output, "r+")
    tmp_file = open("tmp_prob", "w+")
    lines = r1_read.readlines()
    for line in range(4, len(lines), 2):
        tmp_file.write(lines[line])
    tmp_file.close()
    r1_read.close()
    r1_result = pd.read_csv("tmp_prob", delim_whitespace="True", header=None,dtype=str)
    r1_result = r1_result.iloc[:, [1, 4, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]]
    label_list = [
        "particle",
        "MaxLogProb",
        "q1",
        "q2",
        "q3",
        "q4",
        "CTF_amp",
        "CTF_defocus",
        "CTF_B-Env",
        "x_cen",
        "y_cen",
        "normalization",
        "offsett",
    ]
    r1_result.columns = label_list
    # print(r1_result.head(3))
    for ind, particle in r1_result.iterrows():
        CTF_DEFOCUS_VALUE = particle["CTF_defocus"]
        with open(bioEM_template, "r+") as file1:
            with open(working_dir + "/parameters/Parm_%s" % (ind+int(group_now["start"])), "w+") as file2:
                lines = file1.readlines()
                # print(lines)
                for line in lines:
                    line = line.split()
                    if line[0] == "CTF_DEFOCUS":
                        line[1] = CTF_DEFOCUS_VALUE
                        line[2] = CTF_DEFOCUS_VALUE
                        line[3] = 1
                    elif line[0] == "SIGMA_PRIOR_DEFOCUS":
                        line[1] = 0.3
                    string = "  ".join(map(str, line))
                    file2.write(string + "\n")
    # os.remove("tmp_prob")

def making_orientations_submission(
    libraryParmPath,
    r1_foo,
    model_now,
    group_now,
    model_tmp_path,
    model_group_path,
    partition_choice,
    n_node,
    n_cpu,
    path_to_output,
    startFrame
):
    launchOri_workingdir = os.path.join(path_to_output, "1-QMTask")
    os.makedirs(launchOri_workingdir, exist_ok=True)

    launchOri_template_path = os.path.join(
        libraryParmPath, "launch-one-makeOri-template.sh"
    )
    makeOri_template_path = os.path.join(libraryParmPath, "makeOri-template.py")
    # making_ray_slurm_script_file = os.path.join(
    #     libraryParmPath, "making-RAY-SLURM-script.py"
    # )

    shutil.copy(makeOri_template_path, model_tmp_path + "/makeOri.py")
    shutil.copy(launchOri_template_path, launchOri_workingdir + "/launch-one-ori.sh")
    # shutil.copy(making_ray_slurm_script_file, launchOri_workingdir)

    launchOri_workdir_file_path = os.path.join(launchOri_workingdir, "launch-one-ori.sh")
    # making_ray_slurm_script_wordir_file_path = os.path.join(
    #     launchOri_workingdir, "making-RAY-SLURM-script.py"
    # )
    makeOri_slurm_file = os.path.join(libraryParmPath, "slurm-make-ori-template.sh")
    shutil.copy(makeOri_slurm_file, model_tmp_path + "/slurm-make-ori.sh")
    makeOri_slurm_tmp_file_path = os.path.join(model_tmp_path, "slurm-make-ori.sh")
    os.chmod(makeOri_slurm_tmp_file_path, stat.S_IRWXU)

    model_orientation_path = os.path.join(model_group_path, "orientations")
    makeOri_model_tmp_file_path = os.path.join(model_tmp_path, "makeOri.py")

    with open(makeOri_slurm_tmp_file_path,"r") as file:
        slurm_ori = file.read()
        slurm_ori = slurm_ori.replace("WhereOri",makeOri_model_tmp_file_path)
        with open(makeOri_slurm_tmp_file_path,"w") as new:
            new.write(slurm_ori)

    Quat_exe = os.path.join("library", "multiple_Quat", "multiply_quat")
    Quat_exe_abs = os.path.abspath(Quat_exe)
    with open(makeOri_template_path, "r+") as file:
        makeOri_file = file.read()
        makeOri_file = makeOri_file.replace("WhatMODEL", model_now)
        makeOri_file = makeOri_file.replace("WhatGROUP", group_now)
        makeOri_file = makeOri_file.replace("WherePROB", r1_foo)
        makeOri_file = makeOri_file.replace("WhereOrientations", model_orientation_path)
        makeOri_file = makeOri_file.replace("WhereQUAT", Quat_exe_abs)
        makeOri_file = makeOri_file.replace("WhereTOOLKIT",os.path.abspath(os.path.normpath(__file__ + '/../..')))
        makeOri_file = makeOri_file.replace("WhereWORKDIR2",model_group_path)
        makeOri_file = makeOri_file.replace("WhenStart",startFrame)
        makeOri_file = makeOri_file.replace("CPUCOUNT",n_cpu)
        makeOri_file = makeOri_file.replace("NNODE",n_node)

        with open(makeOri_model_tmp_file_path, "w+") as outfile:
            outfile.write(makeOri_file)
    
    # with open(makeOri_slurm_tmp_file_path,"r+") as file:
    #     makeOri_slurm_file = file.read()
    #     makeOri_slurm_file = makeOri_slurm_file.replace("WhatMODEL", model_now)

    if partition_choice is None:
        curdir = os.getcwd()
        os.chdir(model_tmp_path)
        makeOri_cmd = "python makeOri.py"
        subprocess.Popen(makeOri_cmd, shell=True)
        # time.sleep(1)
        os.chdir(curdir)

    else:
        task_path = os.path.join(
            launchOri_workingdir, "CENTRAL_TASK_R2_QM"
        )
        # check_file = os.path.isfile(task_path)
        # check_content = os.path.getsize(task_path)
        # if check_file is True and check_content > 0:
        #     os.remove(task_path)

        with open(task_path, "a+") as task:
            launch_one_command = (
                '%s &> REPORT_R2_QM_%s_%s'
                % (makeOri_slurm_tmp_file_path,model_now,group_now)
            )
            # print(launch_one_command)
            task.write(launch_one_command + "\n")


        # cwd = os.getcwd()
        # os.chdir(launchOri_workingdir)
        # sbatch_cmd = ('sbatch -n %s -c %s -p %s -J %s disBatch %s' % (
        #     n_node,
        #     n_cpu,
        #     partition_choice,
        #     model_now,
        #     task_path,
        # )
        # )
        # subprocess.run(sbatch_cmd,shell=True,check=True)
        # os.chdir(cwd)
    
    
    # if partition_choice is not None:
    #     making_ray_slurm_script_wordir_file_path_abs = os.path.abspath(
    #         making_ray_slurm_script_wordir_file_path
    #     )
    #     with open(making_ray_slurm_script_wordir_file_path_abs, "r+") as file:
    #         make_slurm_launchOne_file = file.read()
    #         make_slurm_launchOne_file = make_slurm_launchOne_file.replace(
    #             "WhereLaunchOne", launchOri_workdir_file_path
    #         )
    #         with open(making_ray_slurm_script_wordir_file_path_abs, "w+") as outfile:
    #             outfile.write(make_slurm_launchOne_file)

        # os.chmod(launchOri_workingdir + "/launch-one-ori.sh", stat.S_IRWXU)
        # return launchOri_workingdir

        # task_path = os.path.join(
        #     launchOri_workingdir, "CENTRAL_TASK_R2_QM"
        # )
        # model_tmp_path = os.path.join(
        #     path_to_output, model_now, "round2", group_now, "tmp_files"
        # )

        # check_file = os.path.isfile(task_path)
        # if check_file is True:
        #     os.remove(task_path)

        # with open(task_path, "a+") as task:
        #     launch_one_command = (
        #         'python %s/making-RAY-SLURM-script.py --exp-name %s --command "python -u %s/makeOri.py "$SLURM_CPUS_PER_TASK"" --partition %s >>out.log'
        #         % (launchOri_workingdir, model_now, model_tmp_path, partition_choice)
        #     )
            # print(launch_one_command)
            # task.write(launch_one_command + "\n")

    #     cwd = os.getcwd()
    #     os.chdir(launchOri_workingdir)
    #     sbatch_cmd = ('sbatch -n %s -c 125 -p %s -J RAY disBatch %s' % (
    #         n_node,
    #         partition_choice,
    #         task_path,
    #     )
    #     )
    #     subprocess.run(sbatch_cmd,shell=True,check=True)
    #     os.chdir(cwd)

    # else:
        # curdir = os.getcwd()
        # os.chdir(model_tmp_path)
        # makeOri_cmd = "python makeOri.py"
        # subprocess.Popen(makeOri_cmd, shell=True)
        # # time.sleep(1)
        # os.chdir(curdir)

def validate_zipfile(path_to_zipfile):
    try:
        with zipfile.ZipFile(path_to_zipfile, "r") as zf:
            print("========== ZIP FILE OK!")
    except zipfile.BadZipFile:
        raise Exception("========== BAD ZIP FILE. ALL FILES ARE SAVED")
    try:
        with zipfile.ZipFile(path_to_zipfile, "r") as zf:
            print("========== ZIP FILE OK!")
    except zipfile.BadZipFile:
        raise Exception("========== BAD ZIP FILE!")

def process_output_round2(delete_choice, MODEL, GROUP, path_to_output, nparticle: int,startFrame, endFrame):
    sorted_output_path = os.path.join(
        path_to_output, "OutPut_SORTED_%s-%s" % (MODEL, GROUP)
    )
    with open(sorted_output_path, "w+") as out_tmp_1:
        with zipfile.ZipFile(
            path_to_output + "/OutPuts_ALL_%s_%s.zip" % (MODEL, GROUP), "w"
        ) as out_zip:
            for i in range(nparticle):
                with open(path_to_output + "/out-%s" % (counter(startFrame,i)), "r+") as out_tmp_2:
                    lines = out_tmp_2.readlines()
                    for line in range(5, len(lines)):
                        line = lines[line].split()
                        if line[2] == "LogProb:":
                            line[1] = counter(startFrame,i)
                            string = "  ".join(map(str, line))
                            out_tmp_1.write(string + "\n")
                            out_tmp_1.flush()
                out_tmp_2.close()
                out_zip.write(
                    path_to_output + "/out-%s" % (counter(startFrame,i)),
                    os.path.basename(path_to_output + "/out-%s" % (i)),
                )
    out_zip.close()
    zipfile_path = os.path.join(
        path_to_output, "OutPuts_ALL_%s_%s.zip" % (MODEL, GROUP)
    )
    if delete_choice == "0":
        try:
            with zipfile.ZipFile(zipfile_path, "r") as zf:
                print("========== ZIP FILE OK! %s cleaned." % (MODEL))
                for i in range(nparticle):
                    os.remove(path_to_output + "/out-%s" % (i))
            zf.close()
        except zipfile.BadZipFile:
            raise Exception("========== BAD ZIP FILE! FILES ARE SAVED.")
    else:
        print("========== Original files will be SAVED.")


def clean_params(delete_choice, MODEL, GROUP, path_to_param, nparticle: int,startFrame, endFrame):
    subparam_list = ["parameters", "orientations"]
    for sub_dir in range(len(subparam_list)):
        group_param_path = os.path.join(path_to_param, subparam_list[sub_dir])
        if os.path.basename(group_param_path) == "parameters":
            with zipfile.ZipFile(
                group_param_path + "/PARM_ALL_%s_%s.zip" % (MODEL, GROUP), "w"
            ) as out_zip:
                for i in range(nparticle):
                    with open(group_param_path + "/Parm_%s" % (counter(startFrame,i)), "r+") as out_tmp:
                        out_zip.write(
                            group_param_path + "/Parm_%s" % (counter(startFrame,i)),
                            os.path.basename(group_param_path + "/Parm_%s" % (i)),
                        )
                    out_tmp.close()
            out_zip.close()
            path_to_zipfile = os.path.join(
                group_param_path, "PARM_ALL_%s_%s.zip" % (MODEL, GROUP)
            )
            validate_zipfile(path_to_zipfile)
            if delete_choice == "0":
                for i in range(nparticle):
                    # print("Parm_%s is removed."%(i))
                    os.remove(group_param_path + "/Parm_%s" % (counter(startFrame,i)))
        elif os.path.basename(group_param_path) == "orientations":
            with zipfile.ZipFile(
                group_param_path + "/ANG_ALL_%s_%s.zip" % (MODEL, GROUP), "w"
            ) as out_zip:
                for i in range(nparticle):
                    with open(
                        group_param_path + "/ANG_R2_%s" % (counter(startFrame,i)), "r+"
                    ) as out_tmp:
                        out_zip.write(
                            group_param_path + "/ANG_R2_%s" % (counter(startFrame,i)),
                            os.path.basename(group_param_path + "/ANG_for-R2-%s" % (i)),
                        )
                    out_tmp.close()
            out_zip.close()
            path_to_zipfile = os.path.join(
                group_param_path, "ANG_ALL_%s_%s.zip" % (MODEL, GROUP)
            )
            validate_zipfile(path_to_zipfile)
            if delete_choice == "0":
                for i in range(nparticle):
                    # print("ANG_for-R2-%s is removed."%(i))
                    os.remove(group_param_path + "/ANG_for-R2-%s" % (i))

    print("========== %s is CLEANED." % (MODEL))

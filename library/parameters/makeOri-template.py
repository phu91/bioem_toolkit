import pandas as pd
import numpy as np
import shutil, stat
import subprocess
import os
import ray
from time import time

ray.init()
print(
    """This cluster consists of
    {} nodes in total
    {} CPU resources in total
""".format(
        len(ray.nodes()), ray.cluster_resources()["CPU"]
    )
)

# def timer_func(func):
#         # This function shows the execution time of
#     # the function object passed
#     def wrap_func(*args, **kwargs):
#         t1 = time()
#         result = func(*args, **kwargs)
#         t2 = time()
#         print(f'Function {func.__name__!r} executed in {(t2-t1):.4f}s')
#         return result
#     return wrap_func

# @timer_func
@ray.remote
def quat_calculation(particle_now):
    trash_collector_path = "."
    grid = 125
    particle_angle = r1_foo_result.loc[(r1_foo_result["particle"] == particle_now)]
    total_orientation = len(particle_angle)
    nTotal_orientation = grid * total_orientation
    tmp_file_path = os.path.join(
        trash_collector_path, "tmp_angle_%s_%s_%s" % (particle_now, MODEL, GROUP)
    )
    with open(tmp_file_path, "w+") as tmp1:
        for ind, orient in particle_angle.iterrows():
            tmp1.write(
                "%12.6f%12.6f%12.6f%12.6f\n"
                % (orient["q1"], orient["q2"], orient["q3"], orient["q4"])
            )
    # print("Run MQ on particle %s"%(particle_now))
    tmp_file_2_path = os.path.join(
        trash_collector_path, "sampling_angle_%s_%s_%s" % (particle_now, MODEL, GROUP)
    )
    multiply_quat_exe = os.path.join(trash_collector_path, "multiply_quat")
    multiple_quat_exe_cmd = "%s %s %s %s" % (
        multiply_quat_exe,
        tmp_file_path,
        tmp_file_2_path,
        grid,
    )
    subprocess.run(multiple_quat_exe_cmd, shell=True)
    ANG_tmp_file_path = os.path.join(
        trash_collector_path, "ANG_for-R2-%s_%s_%s" % (particle_now, MODEL, GROUP)
    )
    with open(ANG_tmp_file_path, "w+") as tmp1:
        tmp1.write(str(nTotal_orientation) + "\n")
        ############################################# PROBLEM: This open nothing!!
        with open(tmp_file_2_path, "r") as tmp2:
            print("Open %s"%(tmp_file_2_path))
            lines = tmp2.readlines()
            for line in lines:
                string = line.split()
                # print(string)
                tmp1.write(
                    "%12.6f%12.6f%12.6f%12.6f\n"
                    % (
                        float(string[0]),
                        float(string[1]),
                        float(string[2]),
                        float(string[3]),
                    )
                )
            # shutil.copy2(tmp2,tmp1)

    shutil.copy(
        ANG_tmp_file_path,
        os.path.join(orientation_path, "ANG_for-R2-%s" % (particle_now)),
    )
    print(":::  %s" % (orientation_path))
    # os.remove(tmp_file_path)
    # os.remove(tmp_file_2_path)
    # os.remove(ANG_tmp_file_path)


# @timer_func
def making_orientations(r1_foo_path, orientations_path):
    global r1_foo_result, orientation_path, MODEL, GROUP
    MODEL = "WhatMODEL"
    GROUP = "WhatGROUP"
    orientation_path = orientations_path
    trash_collector_path = "/tmp"
    shutil.copy("WhereGridFile", trash_collector_path)
    shutil.copy("WhereQUAT", trash_collector_path)
    r1_foo_read = open(r1_foo_path, "r+")
    tmp_file_path = os.path.join(
        trash_collector_path, "tmp_orient_%s_%s" % (MODEL, GROUP)
    )
    tmp_file = open(tmp_file_path, "w+")
    lines = r1_foo_read.readlines()
    for line in range(3, len(lines)):
        tmp_file.write(lines[line])
    tmp_file.close()
    r1_foo_read.close()
    r1_foo_result = pd.read_csv(tmp_file_path, delim_whitespace="True", header=None)
    r1_foo_result = r1_foo_result.iloc[:, [0, 1, 2, 3, 4]]
    label_list = ["particle", "q1", "q2", "q3", "q4"]
    r1_foo_result.columns = label_list
    particle_list = r1_foo_result["particle"].drop_duplicates().values
    ids = [quat_calculation.remote(x) for x in particle_list]
    ray.get(ids)

    # ncpu = multiprocessing.cpu_count()
    # print("There are %s CPUs"%(ncpu))
    # with WorkerPool() as p:
    # p.map(quat_calculation,zip(particle_list))
    # p.close()
    # p.join()


r1_foo_path = "WhereFOO"
orientations_path = "WhereOrientations"
start = time()
CLEAN_P1_FOO = making_orientations
CLEAN_P1_FOO(r1_foo_path, orientations_path)
print("Duration: %s " % (time() - start))

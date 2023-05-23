import pandas as pd
import numpy as np
import shutil, stat
import subprocess
import os
from time import time, sleep
import dask as dd 
from multiprocessing import Pool, cpu_count
from dask.distributed import Client

def quat_calculation(particle_now):
    trash_collector_path = "/dev/shm/"
    toolkit_place_directory = "WhereTOOLKIT"
    grid_num_points = 125
    grid_file= os.path.join(toolkit_place_directory,'bioem_toolkit/library/multiple_Quat/smallGrid_%s'%(grid_num_points))
    particle_angle = r1_prob_result.loc[(r1_prob_result['particle']==particle_now)]
    total_orientation=len(particle_angle)
    nTotal_orientation=grid_num_points*total_orientation
    tmp_file_path = os.path.join(trash_collector_path,"tmp_angle_%s_%s_%s"%(particle_now,MODEL,GROUP))
    with open(tmp_file_path,"w+") as tmp1:
        for ind,orient in particle_angle.iterrows():
            tmp1.write("%12.6f%12.6f%12.6f%12.6f\n"%(orient['q1'],orient['q2'],orient['q3'],orient['q4']))
    print("Run MQ on particle %s"%(particle_now))

    tmp_file_2_path = os.path.join(trash_collector_path,"sampling_angle_%s_%s_%s"%(particle_now,MODEL,GROUP))
    multiply_quat_exe_location = os.path.join(toolkit_place_directory,'bioem_toolkit/library/multiple_Quat/multiply_quat.exe')
    multiple_quat_exe_cmd ="%s %s %s %s"%(multiply_quat_exe_location,os.path.abspath(tmp_file_path),os.path.abspath(tmp_file_2_path),grid_file)
    subprocess.run(multiple_quat_exe_cmd,shell=True,check=True)
    ANG_tmp_file_path = os.path.join(trash_collector_path,"ANG_R2_%s_%s_%s"%(particle_now,MODEL,GROUP))

    with open(ANG_tmp_file_path,'w+') as tmp1:
        tmp1.write(str(nTotal_orientation)+"\n")
    #Its faster to just dump the contents of a file rather than just write it line by line.
    ### PROBLEM: BIOEM ROUND 2 requires a very specific formated strings for the ANGLES. (%12.6f%12.6f%12.6f%12.6)
    ### Can you add this specific formated string into 'cat'?
    # concatenate_command = "cat " +  str(tmp_file_2_path) + " >> " + str(ANG_tmp_file_path)
    # subprocess.run(concatenate_command, shell=True)
        with open(tmp_file_2_path,'r+') as tmp2:
            lines=tmp2.readlines()
            for line in lines:
                string=line.split()
                # print(string)
                tmp1.write("%12.6f%12.6f%12.6f%12.6f\n"%(float(string[0]),float(string[1]),float(string[2]),float(string[3])))
    shutil.copy(ANG_tmp_file_path,os.path.join(orientation_path,"ANG_R2_%s"%(particle_now+WhenStart)))
    os.remove(tmp_file_path)
    os.remove(tmp_file_2_path)
    os.remove(ANG_tmp_file_path)


def making_orientations():
    global r1_prob_result, orientation_path, MODEL,GROUP
    MODEL="WhatMODEL"
    GROUP="WhatGROUP"
    r1_prob="WherePROB"
    workdir_round2="WhereWORKDIR2"  #   INCLUDED GROUP
    orientation_path = os.path.join(workdir_round2,"orientations")
    trash_collector_path = "/dev/shm/"
    os.makedirs(orientation_path,exist_ok=True)
    os.chmod(orientation_path,stat.S_IRWXU)
    r1_prob_read = open(r1_prob,"r+")
    tmp_file_path = os.path.join(trash_collector_path,"tmp_orient_%s_%s"%(MODEL,GROUP))
    tmp_file = open(tmp_file_path,"w+")
    lines = r1_prob_read.readlines()
    for line in range(3,len(lines)):
        tmp_file.write(lines[line])
    tmp_file.close()
    r1_prob_read.close()
    r1_prob_result = pd.read_csv(tmp_file_path,delim_whitespace='True',header=None)
    r1_prob_result = r1_prob_result.iloc[:,[0,1,2,3,4]]
    label_list=["particle","q1","q2","q3","q4"]
    r1_prob_result.columns=label_list
    particle_list = r1_prob_result['particle'].drop_duplicates().values
    return particle_list
# ncpu = 128*2
# print("There are %s CPUs"%(ncpu))
# with Pool(ncpu) as my_pool:
#     my_pool.map(quat_calculation,particle_list)
    # my_pool.close()
    # my_pool.join()

if __name__ == '__main__':
    # client = Client(processes=False)
    start = time()
    particles = making_orientations()
    ncpu = 128
    print("There are %s CPUs"%(ncpu))
    with Pool(ncpu) as my_pool:
        my_pool.map(quat_calculation,particles)
        my_pool.close()
        my_pool.join()
    # print(particles)
    # x= client.map(quat_calculation,particles)
    print("Duration: %s"%(time()-start))
    # client.gather(x)

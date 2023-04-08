import mrcfile as mrc
import sys, os, stat, shutil, argparse, zipfile
import subprocess
import pandas as pd

import numpy as np 
import argparse


parser = argparse.ArgumentParser(description="""
        Here we will create particle stacks for use by bioem. """)

parser.add_argument("-p","--particle-stack",dest="stack", help="Full particle in .mrcs format.")
parser.add_argument("-g","--grouping-file",dest="group_file", default='group_list.txt', help="Textfile to demonstrate how particles should be organised.")
parser.add_argument("-o","--out", dest="output_directory",help="Output directory. Default is particles/..")

args=parser.parse_args()

if args.stack is None:
    raise NameError("You have not specified a particle stack to process with the --particle-stack flag. Script exiting.")

if os.path.exists(args.group_file) == False:
    raise NameError ("Either you have not specified a group file with the --group-file flag or a group file does not exist. ")

group_file_data = np.loadtxt(args.group_file,dtype=str)

with open (args.group_file, 'r') as fp:

    group_data_lines = len (fp.readlines())

#if the group file is only one line long we still need to make sure things are formatted as lists so the rest of the code works.
if group_data_lines == 1:
    write_stack_names = [group_file_data[0]]
    write_stack_directories = [group_file_data[1]]
    write_stack_lengths = [int (group_file_data[2])]

else:
    write_stack_names = group_file_data[:,0]
    write_stack_directories = group_file_data[:,1]
    write_stack_lengths = np.array(group_file_data[:,2],dtype=int)


particles_location = str(os.path.abspath(args.stack))
particles_output_location = str(os.path.abspath(args.output_directory))
#make output directory 
os.makedirs(args.output_directory,exist_ok=True)


#mrc files have a few possible different data formats. Here we are determining which format the file is extracted in.
type_dict = {'int8': 0, 'int16': 1, 'float32': 2,  'complex64': 4, 'uint16': 6}

with mrc.open (particles_location) as temp_mrc:
    x = (temp_mrc.data)

#deciding which format the mrcfile is in. Remember there are a few types. 
type_str = str(x.dtype)
if type_dict [type_str] is None:
    raise KeyError("The .mrcs file you have specified is in a format not recognised by this script. Make edits to line line 35 if to add the format if you know what you are doing. You'll need to check the documentation of the mrcfile python package. ")
mrc_type_int = type_dict[type_str]
print(type_str)

print(np.shape(x))

total_num_particles = (np.shape(x)[0])

#getting single image dimensions.
slice_shape =  list([np.shape(x)[1],np.shape(x)[1]])

for i in range(len(write_stack_directories)):
    os.makedirs(os.path.join(args.output_directory + write_stack_directories[i]),exist_ok=True)
    num_slices = write_stack_lengths[i]
    mrcs_file_shape = [num_slices] + slice_shape 
    mrcs_file_shape = tuple (mrcs_file_shape)
    print(mrcs_file_shape)

    current_stack_location = (particles_output_location + '/' + str(write_stack_names[i]))
    mrc_out_file = mrc.new_mmap(particles_output_location + str(write_stack_names[i]) ,shape=mrcs_file_shape,overwrite=True, mrc_mode = mrc_type_int)

    #mrc_out_file = mrc.new_mmap('temp.mrcs',shape=mrcs_file_shape,overwrite=True, mrc_mode = mrc_type_int)
    #

    for i in range(num_slices):
        mrc_stack_index = i
        #data_line = tuple(data_array[i][2:-1])
        #data_line = ' '.join(data_line)
    #
        mrcs_particle_stack_file = particles_location 
        with mrc.open (mrcs_particle_stack_file) as temp_mrc:
            x = (temp_mrc.data[mrc_stack_index])
            mrc_out_file.data[i] = x
    #    
        np.shape(mrc_out_file.data[i])
        print (i) 
    mrc_out_file.close()

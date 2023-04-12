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
    raise NameError ("Either you have not specified the correct group file with the --group-file flag or a group file does not exist. ")

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


input_particles_location = str(os.path.abspath(args.stack))

#validate mrcfile.
if mrc.validate (input_particles_location):
    print("MRC input file is valid.")
else:
    mrc.validate(input_particles_location)
    raise ArgumentError ("MRC file is not valid. Please check how it was generated.")

particles_output_location = str(os.path.abspath(args.output_directory))
#make output directory 
os.makedirs(args.output_directory,exist_ok=True)


#mrc files have a few possible different data formats. Here we are determining which format the file is extracted in.
type_dict = {'int8': 0, 'int16': 1, 'float32': 2,  'complex64': 4, 'uint16': 6}

with mrc.open (input_particles_location) as temp_mrc:
    x = (temp_mrc.data)

#deciding which format the mrcfile is in. Remember there are a few types. 
type_str = str(x.dtype)
if type_dict [type_str] is None:
    raise KeyError("The .mrcs file you have specified is in a format not recognised by this script. Make edits to line line 35 if to add the format if you know what you are doing. You'll need to check the documentation of the mrcfile python package. ")
mrc_type_int = type_dict[type_str]


total_num_particles = (np.shape(x)[0])

if np.sum(write_stack_lengths) > total_num_particles:
    raise IndexError("You have specified a total of " + str(np.sum(write_stack_lengths)) + " particles in the group file. However, there are only " + str(total_num_particles) + " particles in the full particle stack. Make sure you have constructed the particle stack and the group file correctly.")
elif np.sum(write_stack_lengths) < total_num_particles: 
    print("Warning: Using less than all the particles in the full stack. If this was not intended check the group file.")
else: 
    print("Using full particle stack.")

#getting single image dimensions.
slice_shape =  list([np.shape(x)[1],np.shape(x)[1]])

running_particle_index = 0 
for i in range(len(write_stack_directories)):
    os.makedirs(os.path.join(particles_output_location + '/' + write_stack_directories[i]),exist_ok=True)
    single_mrc_file_shape = [1] + slice_shape 
    single_mrc_file_shape = tuple (single_mrc_file_shape)

    mrcs_stack_file_shape = [write_stack_lengths[i]] + slice_shape 
    mrcs_stack_file_shape = tuple (mrcs_stack_file_shape)

    current_stack_location = (particles_output_location + '/' + str(write_stack_names[i]))

    mrcs_stack_out_file = mrc.new_mmap(particles_output_location + '/' + str(write_stack_names[i] ) ,shape=mrcs_stack_file_shape,overwrite=True, mrc_mode = mrc_type_int)

    #will need to make this faster when we move to large particle datasets. Remeber, we need to write out each individual particle to an mrc file AND output each group as a stack of .mrcs files (even though this is redundant).
    for j in range(write_stack_lengths[i]):
        with mrc.open (input_particles_location,permissive=True) as temp_mrc:

            current_image = (temp_mrc.data[running_particle_index])
            mrcs_stack_out_file.data[j] = current_image
            
            single_mrc_out_file = mrc.new_mmap(particles_output_location + '/' + str(write_stack_directories[i]) + '/' + 'particle_' +str(running_particle_index) + '.mrc' , shape=single_mrc_file_shape,overwrite=True, mrc_mode = mrc_type_int)
            single_mrc_out_file.data[0] = current_image
            running_particle_index = running_particle_index + 1
            print (j)
            single_mrc_out_file.close()
#    
    #for i in range(num_slices):
    mrcs_stack_out_file.close()

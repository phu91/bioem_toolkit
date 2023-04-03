#!/usr/bin/env python

import sys, os, stat, shutil, argparse, zipfile
import subprocess
import pandas as pd
import mrcfile as mrc
import numpy as np
# from multiprocessing import Process


def clean_R1_Probability(working_dir,r1_output:str,bioEM_template):
	r1_read = open(r1_output,"r+")
	tmp_file = open("tmp_prob","w+")
	lines = r1_read.readlines()
	for line in range(4,len(lines),2):
		tmp_file.write(lines[line])
	tmp_file.close()
	r1_read.close()
	r1_result = pd.read_csv("tmp_prob",delim_whitespace='True',header=None)
	r1_result = r1_result.iloc[:,[1,4,5,7,9,11,13,15,17,19,21,23,25]]
	label_list=["particle","MaxLogProb","q1","q2","q3","q4","CTF_amp","CTF_defocus","CTF_B-Env","x_cen","y_cen","normalization","offsett"]
	r1_result.columns=label_list
	# print(r1_result.head(3))
	for ind, particle in r1_result.iterrows():
		CTF_DEFOCUS_VALUE = particle['CTF_defocus']
		with open(bioEM_template,"r+") as file1:
			with open(working_dir+"/parameters/Parm_%s"%(ind),"w+") as file2:
				lines = file1.readlines()
				# print(lines)
				for line in lines:
					line = line.split()
					if line[0]=="CTF_DEFOCUS":
						line[1]=CTF_DEFOCUS_VALUE
						line[2]=CTF_DEFOCUS_VALUE
						line[3]=1
					elif line[0]=="SIGMA_PRIOR_DEFOCUS":
						line[1]=0.3	
					string = '  '.join(map(str,line))
					file2.write(string+"\n")
		file1.close()
		file2.close()
	# os.remove("tmp_prob")

def making_orientations(r1_foo,workdir_round2):
	grid=125
	r1_foo_read = open(r1_foo,"r+")
	tmp_file = open("tmp_orient","w+")
	lines = r1_foo_read.readlines()
	for line in range(3,len(lines)):
		tmp_file.write(lines[line])
	tmp_file.close()
	r1_foo_read.close()
	r1_foo_result = pd.read_csv("tmp_orient",delim_whitespace='True',header=None)
	r1_foo_result = r1_foo_result.iloc[:,[0,1,2,3,4]]
	label_list=["particle","q1","q2","q3","q4"]
	r1_foo_result.columns=label_list
	# os.remove("tmp_orient")
	particle_list = r1_foo_result['particle'].drop_duplicates().values
	# print(particle_list.values[0])
	for particle_index in range(len(particle_list)):
		# print(particle_index)
		particle_now = particle_list[particle_index]
		particle_angle = r1_foo_result.loc[(r1_foo_result['particle']==particle_now)]
		total_orientation=len(particle_angle)
		nTotal_orientation=grid*total_orientation
		with open("tmp_angle_%s"%(particle_now),"w+") as tmp1:
			for ind,orient in particle_angle.iterrows():
				tmp1.write("%12.6f%12.6f%12.6f%12.6f\n"%(orient['q1'],orient['q2'],orient['q3'],orient['q4']))
		tmp1.close()
		print("Run MQ on particle %s"%(particle_now))
		multiple_quat_exe_cmd ="/mnt/home/ptang/ceph/6-ABC-Transporter/1-PROCESSING/trial2/library/multiple_Quat/multiply_quat.exe tmp_angle_%s sampling_angle_%s %s"%(particle_now,particle_now,grid)
		subprocess.run(multiple_quat_exe_cmd,shell=True)
		with open("ANG_for-R2-%s"%(particle_now),'w+') as tmp1:
			tmp1.write(str(nTotal_orientation)+"\n")
			for f in ["sampling_angle_%s"%(particle_now)]:
				with open(f,'r+') as tmp2:
					lines=tmp2.readlines()
					for line in lines:
						string=line.split()
						# print(string)
						tmp1.write("%12.6f%12.6f%12.6f%12.6f\n"%(float(string[0]),float(string[1]),float(string[2]),float(string[3])))
					# shutil.copy2(tmp2,tmp1)
				tmp2.close()
		tmp1.close()
		shutil.copy("ANG_for-R2-%s"%(particle_now),os.path.join(workdir_round2,"orientations"))
		os.remove("tmp_angle_%s"%(particle_now))
		os.remove("sampling_angle_%s"%(particle_now))
		os.remove("ANG_for-R2-%s"%(particle_now))
		# return particle_now

def validate_zipfile(path_to_zipfile):
	try:
		with zipfile.ZipFile(path_to_zipfile,"r") as zf:
			print("========== ZIP FILE OK!")
	except zipfile.BadZipFile:
		raise Exception("========== BAD ZIP FILE. ALL FILES ARE SAVED")
	try:
		with zipfile.ZipFile(path_to_zipfile,"r") as zf:
			print("========== ZIP FILE OK!")
	except zipfile.BadZipFile:
		raise Exception("========== BAD ZIP FILE!")

def process_output_round2(delete_choice,MODEL,GROUP,path_to_output,nparticle: int):
    	sorted_output_path=os.path.join(path_to_output,"OutPut_SORTED_%s-%s"%(MODEL,GROUP))
	with open(sorted_output_path,"w+") as out_tmp_1:
		with zipfile.ZipFile(path_to_output+"/OutPuts_ALL_%s_%s.zip"%(MODEL,GROUP),"w") as out_zip:
			for i in range(nparticle):
				with open(path_to_output+"/out-%s"%(i),"r+") as out_tmp_2:
					lines = out_tmp_2.readlines()
					for line in range(5,len(lines)):
						line = lines[line].split()
						if line[2]=="LogProb:":
							line[1]=i
							string = '  '.join(map(str,line))
							out_tmp_1.write(string+"\n")
							out_tmp_1.flush()
				out_tmp_2.close()
				out_zip.write(path_to_output+"/out-%s"%(i),os.path.basename(path_to_output+"/out-%s"%(i)))
	out_zip.close()
	zipfile_path=os.path.join(path_to_output,"OutPuts_ALL_%s_%s.zip"%(MODEL,GROUP))
	if delete_choice=='0':
		try:
			with zipfile.ZipFile(zipfile_path,"r") as zf:
				print("========== ZIP FILE OK! %s cleaned."%(MODEL))
				for i in range(nparticle):
					os.remove(path_to_output+"/out-%s"%(i))
			zf.close()
		except zipfile.BadZipFile:
			raise Exception("========== BAD ZIP FILE! FILES ARE SAVED.")
	else:
		print("========== Original files will be SAVED.")

def clean_params(delete_choice,MODEL,GROUP,path_to_param,nparticle: int):
	subparam_list = ['parameters','orientations']
	for sub_dir in range(len(subparam_list)):
		group_param_path=os.path.join(path_to_param,subparam_list[sub_dir])
		if os.path.basename(group_param_path)=="parameters":
			with zipfile.ZipFile(group_param_path+"/PARM_ALL_%s_%s.zip"%(MODEL,GROUP),"w") as out_zip:
				for i in range(nparticle):
					with open(group_param_path+"/Parm_%s"%(i),"r+") as out_tmp:
						out_zip.write(group_param_path+"/Parm_%s"%(i),os.path.basename(group_param_path+"/Parm_%s"%(i)))
					out_tmp.close()
			out_zip.close()
			path_to_zipfile=os.path.join(group_param_path,"PARM_ALL_%s_%s.zip"%(MODEL,GROUP))
			validate_zipfile(path_to_zipfile)
			if delete_choice=='0':
				for i in range(nparticle):
					# print("Parm_%s is removed."%(i))
					os.remove(group_param_path+"/Parm_%s"%(i))
		elif os.path.basename(group_param_path)=="orientations":
			with zipfile.ZipFile(group_param_path+"/ANG_ALL_%s_%s.zip"%(MODEL,GROUP),"w") as out_zip:
				for i in range(nparticle):
					with open(group_param_path+"/ANG_for-R2-%s"%(i),"r+") as out_tmp:
						out_zip.write(group_param_path+"/ANG_for-R2-%s"%(i),os.path.basename(group_param_path+"/ANG_for-R2-%s"%(i)))
					out_tmp.close()
			out_zip.close()
			path_to_zipfile=os.path.join(group_param_path,"ANG_ALL_%s_%s.zip"%(MODEL,GROUP))
			validate_zipfile(path_to_zipfile)
			if delete_choice=='0':
				for i in range(nparticle):
					# print("ANG_for-R2-%s is removed."%(i))
					os.remove(group_param_path+"/ANG_for-R2-%s"%(i))

	print("========== %s is CLEANED."%(MODEL))


#################################### NORMAL CLASSES
class NORMAL_MODE_ROUND1:
	"""A simple example class"""
	def __init__(self,model_path,model_list,group_list,param_path,particle_path,output_path):
		self.model_path = model_path
		self.model_list = model_list
		self.group_list = group_list
		self.param_path  = param_path
		self.particle_path = particle_path
		self.output_path = output_path

	def PREP(self):
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()

		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		# print(GROUPS)
		# Strips the newline character
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			a_model_path = os.path.join(op_v,MODEL)
			os.makedirs(a_model_path,exist_ok='True')
			os.makedirs(os.path.join(a_model_path,"round1"),exist_ok='True')

			for ind, GROUP in GROUPS.iterrows():
				round1_path = os.path.join(a_model_path,"round1")
				r1_group_path =os.path.join(round1_path,GROUP['group'])
				os.makedirs(r1_group_path,exist_ok='True')

				shutil.copy(os.path.join(mp_v,MODEL+".txt"),a_model_path)
				shutil.copy(param_v+"/Param_BioEM_ABC_template",round1_path+"/Param_BioEM_ABC")
				shutil.copy(param_v+"/Quat_36864",round1_path)

				with open(param_v+"/slurm-r1-template.sh",'r+') as file:
					slurm_file = file.read()
					slurm_file_out_path =str(r1_group_path)+"/slurm-r1-rusty.sh"
					# print(slurm_file_out_path)
					slurm_file = slurm_file.replace('WhereSlurm',r1_group_path)
					slurm_file = slurm_file.replace('WhatModel', MODEL)
					slurm_file = slurm_file.replace('WhereParticle',os.path.join(self.particle_path,GROUP['particle_file']))
					slurm_file = slurm_file.replace('WhatGroup', GROUP['group'])

					with open(slurm_file_out_path,'w+') as outfile:
						outfile.write(slurm_file)
					outfile.close()
				file.close()

	def RUN(self,choice):
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			a_model_path = os.path.join(op_v,MODEL)
			round1_path = os.path.join(a_model_path,"round1")
			GROUP=None
			if choice=="A" or choice =="a":
				for ind, GROUP in GROUPS.iterrows():
					r1_group_path =os.path.join(round1_path,GROUP['group'])
					slurm_file_out_path =os.path.join(r1_group_path,"slurm-r1-rusty.sh")
					os.chmod(slurm_file_out_path,stat.S_IRWXU)
					# print(slurm_file_out_path)
					os.chdir(r1_group_path)
					sbatch_cmd = "sbatch "+slurm_file_out_path
					subprocess.run(str(sbatch_cmd),shell=True, check=True)
			else:
				GROUP=choice
				r1_group_path =os.path.join(round1_path,GROUP)
				slurm_file_out_path =str(r1_group_path)+"/slurm-r1-rusty.sh"
				os.chmod(r1_group_path+"/slurm-r1-rusty.sh",stat.S_IRWXU)
				# print(slurm_file_out_path)
				sbatch_cmd = "sbatch "+slurm_file_out_path
				subprocess.run(str(sbatch_cmd),shell=True, check=True)


class NORMAL_MODE_ROUND2:
	def __init__(self,model_path,model_list,group_list,param_path,particle_path,output_path):
		self.model_path = model_path
		self.model_list = model_list
		self.group_list = group_list
		self.param_path  = param_path
		self.particle_path = particle_path
		self.output_path = output_path


	def PREP(self):
		# global task_path
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()

		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],
											delim_whitespace='True',comment='#')
		# print(GROUPS)
		# Strips the newline character
		for MODEL in MODELS:
			MODEL=MODEL.strip()
			if MODEL[0]=='#':
				print("%s is skipped."%(MODEL[1:]))
				continue
			a_model_path = os.path.join(op_v,MODEL)
			os.makedirs(a_model_path,exist_ok='True')
			os.makedirs(os.path.join(a_model_path,"round2"),exist_ok='True')
			round1_path = os.path.join(a_model_path,"round1")

			for ind, GROUP in GROUPS.iterrows():
				round2_path = os.path.join(a_model_path,"round2")
				r1_group_path =os.path.join(round1_path,GROUP['group'])
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				os.makedirs(r2_group_path,exist_ok='True')
				subdir_list = ['/parameters','/orientations','/tasks','/outputs','/tmp_files']

				for sub_dir in range(len(subdir_list)):
					os.makedirs(r2_group_path+subdir_list[sub_dir],exist_ok='True')
					group_param_path=os.path.join(r2_group_path+subdir_list[sub_dir])

					if os.path.basename(group_param_path)=="tmp_files":
						shutil.copy(param_v+"Param_BioEM_ABC_template",group_param_path)
						param_bio_template_path = os.path.join(group_param_path,"Param_BioEM_ABC_template")
						shutil.copy(r1_group_path+"/Output_Probabilities",group_param_path+"/Output_Probabilities-R1")
						Out_Prob_R1_path = os.path.join(group_param_path,"Output_Probabilities-R1")

						CLEAN_P1_PROB = clean_R1_Probability
						CLEAN_P1_PROB(r2_group_path,Out_Prob_R1_path,param_bio_template_path)
						print("========== Done with PARAMETER FILES for %s"%(MODEL))

						shutil.copy(r1_group_path+"/foo.txt",group_param_path+"/PROB_ANGLE_R1.txt")
						CLEAN_P1_FOO = making_orientations
						CLEAN_P1_FOO(group_param_path+"/PROB_ANGLE_R1.txt",r2_group_path)
						print("========== Done with ORIENTATION FILES for %s"%(MODEL))

					elif os.path.basename(group_param_path)=="tasks":
					# if os.path.basename(group_param_path)=="tasks":   # FOR TESTING
						shutil.copy(param_v+"launch-one-template.sh",group_param_path)
						launch_one_path = os.path.join(group_param_path,"launch-one-template.sh")
						# print(launch_one_path)
						with open(launch_one_path,"r+") as launchIn:
							with open(group_param_path+"/launch-one.sh","w+") as launchOut:
								lines = launchIn.readlines()
								for line in lines:
									line = line.split()
									# print(line)
									if len(line)>=2:
										if line[1]=="SLURM_JOB_NAME=WhatModel-R2":
											line[1]="SLURM_JOB_NAME=%s-R2"%(MODEL)
										elif line[1]=="WhereRound2=WhereRound2":
											line[1]="WhereRound2=%s"%(round2_path)
										elif line[1]=="WhereParticles=WhereParticles":
											line[1]="WhereParticles=%s"%(self.particle_path)
										elif line[1]=="WhereModel=WhereModel":
											line[1]="WhereModel=%s"%(os.path.abspath(self.model_path))
									# print(*line)
									string = '  '.join(map(str,line))
									launchOut.write(string+"\n")
								launchOut.close()
						launchIn.close()
						os.chmod(group_param_path+"/launch-one.sh",stat.S_IRWXU)
						# os.remove(launch_one_path)

						task_path = os.path.join(group_param_path,"task_%s_%s"%(MODEL,GROUP['group']))
						particle_count = GROUP['nframe']
						with open(task_path,"w+") as task:
							for i in range(particle_count):
								# print(i)
								launch_one_command="./launch-one.sh %s %s %s  &>> out.log"%(i,GROUP['group'],MODEL)
								task.write(launch_one_command+"\n")
						task.close()
						print("========== Done with creating Task File for %s"%(MODEL))


	def RUN(self):
		try:
			subprocess.check_output(["disBatch", "--help"], stderr=subprocess.STDOUT).decode("utf8")
			print("\ndisBatch is LOADED. SUBMIT JOBS NOW!\n")
			MODELS_LIST = open(self.model_list)
			MODELS = MODELS_LIST.readlines()
			GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
			for MODEL in MODELS:
				MODEL = MODEL.strip()
				if MODEL[0]=='#':
					print("%s is skipped."%(MODEL[1:]))
					continue
				a_model_path = os.path.join(op_v,MODEL)
				round2_path = os.path.join(a_model_path,"round2")
				GROUP=None
				for ind, GROUP in GROUPS.iterrows():
					r2_group_path =os.path.join(round2_path,GROUP['group'])
					task_path = os.path.join(r2_group_path,"tasks")
					# task_file_path =os.path.join(task_path,"task_%s_%s"%(MODEL,GROUP['group']))
					# print(task_file_path)
					task_file_name="task_%s_%s"%(MODEL,GROUP['group'])
					os.chdir(task_path)
					sbatch_cmd = "sbatch -p ccm -J %s -t 125 disBatch %s"%(MODEL,task_file_name)
					# print(os.getcwd(),sbatch_cmd)
					subprocess.run(sbatch_cmd,shell=True)
		except:
			print("\nYou need to load disBatch to launch ROUND 2. PROGRAM TERMINATED!!!\n")

	def CLEAN(self):
		delete_choice = input("Do you want to keep the original files? Choose (0) NO or (1) YES\n")
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			if MODEL[0]=='#':
				print("%s is skipped."%(MODEL[1:]))
				continue

			a_model_path = os.path.join(op_v,MODEL)
			round2_path = os.path.join(a_model_path,"round2")
			GROUP=None
			print("\n========== Now cleaning %s"%(MODEL))
			for ind, GROUP in GROUPS.iterrows():
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				path_to_your_mess = os.path.join(r2_group_path,"outputs")
				process_output_round2(delete_choice,MODEL,GROUP['group'],path_to_your_mess,GROUP['nframe'])

	def CLEAN_PARAMS(self):
		delete_choice = input("Do you want to keep the original files? Choose (0) NO or (1) YES\n")
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			if MODEL[0]=='#':
				print("%s is skipped."%(MODEL[1:]))
				continue
			a_model_path = os.path.join(op_v,MODEL)
			round2_path = os.path.join(a_model_path,"round2")
			GROUP=None
			print("========== Now cleaning %s"%(MODEL))
			for ind, GROUP in GROUPS.iterrows():
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				clean_params(delete_choice,MODEL,GROUP['group'],r2_group_path,GROUP['nframe'])


#################################### CONSENSUS CLASSES
class CONSENSUS_MODE_ROUND_1:
	def __init__(self,model_path,model_list,group_list,param_path,particle_path,output_path):
		self.model_path = model_path
		self.model_list = model_list
		self.group_list = group_list
		self.param_path  = param_path
		self.particle_path = particle_path
		self.output_path = output_path

	def PREP(self):
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		consensus_MODEL_name = input("Please provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		os.makedirs(consensus_MODEL_path,exist_ok='True')
		MODEL = consensus_MODEL_name
		print("========== CONSENSUS PATH: %s"%(consensus_MODEL_path))

		round1_path = os.path.join(consensus_MODEL_path,"round1")
		os.makedirs(round1_path,exist_ok='True')

		for ind, GROUP in GROUPS.iterrows():
			r1_group_path =os.path.join(round1_path,GROUP['group'])
			os.makedirs(r1_group_path,exist_ok='True')
			shutil.copy(os.path.join(mp_v,MODEL+".txt"),consensus_MODEL_path)
			shutil.copy(param_v+"/Param_BioEM_ABC_template",round1_path+"/Param_BioEM_ABC")
			shutil.copy(param_v+"/Quat_36864",round1_path)
			with open(param_v+"/slurm-r1-template.sh",'r+') as file:
				slurm_file = file.read()
				slurm_file_out_path =str(r1_group_path)+"/slurm-r1-rusty.sh"
				# print(slurm_file_out_path)
				slurm_file = slurm_file.replace('WhereSlurm',r1_group_path)
				slurm_file = slurm_file.replace('WhatModel', MODEL)
				slurm_file = slurm_file.replace('WhereParticle',os.path.join(self.particle_path,GROUP['particle_file']))
				slurm_file = slurm_file.replace('WhatGroup', GROUP['group'])
				with open(slurm_file_out_path,'w+') as outfile:
					outfile.write(slurm_file)
				outfile.close()
			file.close()
			print("PREPPING CONSENSUS DONE!")

	def RUN(self):
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		consensus_MODEL_name = input("Please provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		print("\n========== CONSENSUS PATH: %s"%(consensus_MODEL_path))
		round1_path = os.path.join(consensus_MODEL_path,"round1")
		for ind, GROUP in GROUPS.iterrows():
			r1_group_path =os.path.join(round1_path,GROUP['group'])
			slurm_file_out_path =os.path.join(r1_group_path,"slurm-r1-rusty.sh")
			os.chmod(slurm_file_out_path,stat.S_IRWXU)
			# print(slurm_file_out_path)
			os.chdir(r1_group_path)
			sbatch_cmd = "sbatch "+slurm_file_out_path
			subprocess.run(str(sbatch_cmd),shell=True, check=True)

class CONSENSUS_MODE_ROUND_2:
	def __init__(self,model_path,model_list,group_list,param_path,particle_path,output_path):
		self.model_path = model_path
		self.model_list = model_list
		self.group_list = group_list
		self.param_path  = param_path
		self.particle_path = particle_path
		self.output_path = output_path

	def PREP_NONCONSENSUS(self):
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		consensus_MODEL_name = input("\n========== Please provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		for MODEL in MODELS:
			MODEL=MODEL.strip()
			if MODEL[0]=='#':
				print("\n========== Models to be skip:")
				print("%s is skipped."%(MODEL[1:]))
				continue
			elif MODEL==consensus_MODEL_name:
				continue
			# print(consensus_MODEL_path)
			a_model_path = os.path.join(op_v,MODEL)
			os.makedirs(a_model_path,exist_ok='True')
			os.makedirs(os.path.join(a_model_path,"round2"),exist_ok='True')
			round1_path = os.path.join(a_model_path,"round1")

			for ind, GROUP in GROUPS.iterrows():
				consensus_round1_path = os.path.join(consensus_MODEL_path,"round1")
				consensus_round2_path = os.path.join(consensus_MODEL_path,"round2")
				consensus_round1_group_path =os.path.join(consensus_round1_path,GROUP['group'])
				consensus_round2_group_path =os.path.join(consensus_round2_path,GROUP['group'])
				# print(consensus_round2_group_path)
				round2_path = os.path.join(a_model_path,"round2")
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				os.makedirs(r2_group_path,exist_ok='True')
				subdir_list = ['/tasks','/outputs','/tmp_files']

				for sub_dir in range(len(subdir_list)):
					os.makedirs(r2_group_path+subdir_list[sub_dir],exist_ok='True')
					group_param_path=os.path.join(r2_group_path+subdir_list[sub_dir])

					if os.path.basename(group_param_path)=="tasks":
					# if os.path.basename(group_param_path)=="tasks":   # FOR TESTING
						launch_one_template_path = os.path.join(self.param_path,"launch-one-NONCONSENSUS-template.sh")
						shutil.copy(launch_one_template_path,group_param_path)
						launch_one_path = os.path.join(group_param_path,"launch-one-NONCONSENSUS-template.sh")
						# print(launch_one_path)
						with open(launch_one_path,"r+") as launchIn:
							with open(group_param_path+"/launch-one.sh","w+") as launchOut:
								lines = launchIn.readlines()
								for line in lines:
									line = line.split()
									# print(line)
									if len(line)>=2:
										if line[1]=="SLURM_JOB_NAME=WhatModel-R2":
											line[1]="SLURM_JOB_NAME=%s-R2"%(MODEL)
										elif line[1]=="WhereRound2CM=WhereRound2CM":
											# print(consensus_round2_group_path)
											line[1]="WhereRound2CM=%s"%(consensus_round2_path)
										elif line[1]=="WhereParticles=WhereParticles":
											line[1]="WhereParticles=%s"%(self.particle_path)
										elif line[1]=="WhereModel=WhereModel":
											line[1]="WhereModel=%s"%(os.path.abspath(self.model_path))
										elif line[1]=="WhereOutput=WhereOutput":
											line[1]="WhereOutput=%s"%(round2_path)
											# print(round2_path)
									# print(*line)
									string = '  '.join(map(str,line))
									launchOut.write(string+"\n")
								launchOut.close()
						launchIn.close()
						os.chmod(group_param_path+"/launch-one.sh",stat.S_IRWXU)
						# os.remove(launch_one_path)

						task_path = os.path.join(group_param_path,"task_%s_%s"%(MODEL,GROUP['group']))
						particle_count = GROUP['nframe']
						with open(task_path,"w+") as task:
							for i in range(particle_count):
								# print(i)
								launch_one_command="./launch-one.sh %s %s %s  &>> out.log"%(i,GROUP['group'],MODEL)
								task.write(launch_one_command+"\n")
						task.close()
						print("\n========== Done with TASK FILES for NON-CONSENSUS %s"%(MODEL))
		print("\n========== CONSENSUS PATH: %s"%(consensus_MODEL_path))

	def PREP_CONSENSUS(self):
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		consensus_MODEL_name = input("\n========== Please provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		os.makedirs(consensus_MODEL_path,exist_ok='True')
		os.makedirs(os.path.join(consensus_MODEL_path,"round2"),exist_ok='True')
		consensus_round1_path = os.path.join(consensus_MODEL_path,"round1")
		consensus_round2_path = os.path.join(consensus_MODEL_path,"round2")

		for ind, GROUP in GROUPS.iterrows():
			consensus_round1_group_path =os.path.join(consensus_round1_path,GROUP['group'])
			consensus_round2_group_path =os.path.join(consensus_round2_path,GROUP['group'])
			# print(consensus_round2_group_path)

			os.makedirs(consensus_round2_group_path,exist_ok='True')
			subdir_list = ['/parameters','/orientations','/tasks','/outputs','/tmp_files']

			for sub_dir in range(len(subdir_list)):
				os.makedirs(consensus_round2_group_path+subdir_list[sub_dir],exist_ok='True')
				group_param_path=os.path.join(consensus_round2_group_path+subdir_list[sub_dir])

				if os.path.basename(group_param_path)=="tmp_files":
					# self.param_path+"Param_BioEM_ABC_template"
					param_bio_R1_path = os.path.join(consensus_round1_path,"Param_BioEM_ABC")
					shutil.copy(param_bio_R1_path,group_param_path)
					output_prob_from_R1 = os.path.join(consensus_round1_group_path,"Output_Probabilities")
					Out_copied_Prob_R1_path = os.path.join(group_param_path,"Output_Probabilities-R1")
					shutil.copy(output_prob_from_R1,Out_copied_Prob_R1_path)
					CLEAN_P1_PROB = clean_R1_Probability
					CLEAN_P1_PROB(consensus_round2_group_path,Out_copied_Prob_R1_path,param_bio_R1_path)
					print("========== Done with PARAMETER FILES for %s"%(consensus_MODEL_name))
					shutil.copy(consensus_round1_group_path+"/foo.txt",group_param_path+"/PROB_ANGLE_R1.txt")
					CLEAN_P1_FOO = making_orientations
					CLEAN_P1_FOO(group_param_path+"/PROB_ANGLE_R1.txt",consensus_round2_group_path)
					print("========== Done with ORIENTATION FILES for %s"%(consensus_MODEL_name))

				elif os.path.basename(group_param_path)=="tasks":
				# if os.path.basename(group_param_path)=="tasks":   # FOR TESTING
					launch_one_template_path = os.path.join(self.param_path,"launch-one-template.sh")
					shutil.copy(launch_one_template_path,group_param_path)
					launch_one_path = os.path.join(group_param_path,"launch-one-template.sh")
					# print(launch_one_path)
					with open(launch_one_path,"r+") as launchIn:
						with open(group_param_path+"/launch-one.sh","w+") as launchOut:
							lines = launchIn.readlines()
							for line in lines:
								line = line.split()
								# print(line)
								if len(line)>=2:
									if line[1]=="SLURM_JOB_NAME=WhatModel-R2":
										line[1]="SLURM_JOB_NAME=%s-R2"%(consensus_MODEL_name)
									elif line[1]=="WhereRound2=WhereRound2":
										# print(consensus_round2_group_path)
										line[1]="WhereRound2=%s"%(consensus_round2_path)
									elif line[1]=="WhereParticles=WhereParticles":
										line[1]="WhereParticles=%s"%(self.particle_path)
									elif line[1]=="WhereModel=WhereModel":
										line[1]="WhereModel=%s"%(os.path.abspath(self.model_path))
								# print(*line)
								string = '  '.join(map(str,line))
								launchOut.write(string+"\n")
							launchOut.close()
					launchIn.close()
					os.chmod(group_param_path+"/launch-one.sh",stat.S_IRWXU)
					# os.remove(launch_one_path)
					task_path = os.path.join(group_param_path,"task_%s_%s"%(consensus_MODEL_name,GROUP['group']))
					particle_count = GROUP['nframe']
					with open(task_path,"w+") as task:
						for i in range(particle_count):
							# print(i)
							launch_one_command="./launch-one.sh %s %s %s  &>> out.log"%(i,GROUP['group'],consensus_MODEL_name)
							task.write(launch_one_command+"\n")
					task.close()
					print("\n========== Done with TASK FILES for CONSENSUS MODEL: %s"%(consensus_MODEL_name))
		# print("\n========== CONSENSUS PATH: %s"%(consensus_MODEL_path))

	def RUN_NONCONSENSUS(self):
		try:
			subprocess.check_output(["disBatch", "--help"], stderr=subprocess.STDOUT).decode("utf8")
			print("========== disBatch is LOADED. SUBMIT JOBS NOW!")
		except:
			print("\nYou need to load disBatch to launch ROUND 2. PROGRAM TERMINATED!!!\n")
			exit

		consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			if MODEL[0]=='#':
				# print("%s is skipped."%(MODEL[1:]))
				continue
			elif MODEL==consensus_MODEL_name:
				continue
			a_model_path = os.path.join(op_v,MODEL)
			round2_path = os.path.join(a_model_path,"round2")
			GROUP=None
			for ind, GROUP in GROUPS.iterrows():
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				task_path = os.path.join(r2_group_path,"tasks")
				task_file_name="task_%s_%s"%(MODEL,GROUP['group'])
				os.chdir(task_path)
				sbatch_cmd = "sbatch -p ccm -J %s -t 125 disBatch %s"%(MODEL,task_file_name)
				# print(sbatch_cmd)
				subprocess.run(sbatch_cmd,shell=True)

	def RUN_CONSENSUS(self):
		try:
			subprocess.check_output(["disBatch", "--help"], stderr=subprocess.STDOUT).decode("utf8")
			print("========== disBatch is LOADED. SUBMIT JOBS NOW!")
		except:
			print("\nYou need to load disBatch to launch ROUND 2. PROGRAM TERMINATED!!!\n")
			exit

		consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		round2_path = os.path.join(consensus_MODEL_path,"round2")
		GROUP=None
		for ind, GROUP in GROUPS.iterrows():
			r2_group_path =os.path.join(round2_path,GROUP['group'])
			task_path = os.path.join(r2_group_path,"tasks")
			task_file_name="task_%s_%s"%(consensus_MODEL_name,GROUP['group'])
			os.chdir(task_path)
			sbatch_cmd = "sbatch -p ccm -J %s -t 125 disBatch %s"%(consensus_MODEL_name,task_file_name)
			# print(sbatch_cmd)
			subprocess.run(sbatch_cmd,shell=True)

	def CLEAN_OUTPUT_NONCONSENSUS(self):
		consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			if MODEL[0]=='#':
				# print("%s is skipped."%(MODEL[1:]))
				continue
			elif MODEL==consensus_MODEL_name:
				continue
			a_model_path = os.path.join(op_v,MODEL)
			round2_path = os.path.join(a_model_path,"round2")
			GROUP=None
			print("========== Now cleaning %s"%(MODEL))
			for ind, GROUP in GROUPS.iterrows():
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				path_to_your_mess = os.path.join(r2_group_path,"outputs")
				process_output_round2(MODEL,GROUP['group'],path_to_your_mess,GROUP['nframe'])

	def CLEAN_OUTPUT_CONSENSUS(self):
		consensus_MODEL_name = input("\nPlease provide the CONSENSUS MODEL NAME:\n")
		consensus_MODEL_path = os.path.join(self.output_path,consensus_MODEL_name)
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		round2_path = os.path.join(consensus_MODEL_path,"round2")
		GROUP=None
		print("========== Now cleaning CONSENSUS MODEL %s"%(consensus_MODEL_name))
		for ind, GROUP in GROUPS.iterrows():
			r2_group_path =os.path.join(round2_path,GROUP['group'])
			path_to_your_mess = os.path.join(r2_group_path,"outputs")
			process_output_round2(consensus_MODEL_name,GROUP['group'],path_to_your_mess,GROUP['nframe'])

	def CLEAN_PARAMS(self):
		delete_choice = input("Do you want to keep the original files? Choose (0) NO or (1) YES\n")
		MODELS_LIST = open(self.model_list)
		MODELS = MODELS_LIST.readlines()
		GROUPS = pd.read_csv(self.group_list,names=['particle_file','group','nframe'],delim_whitespace='True',comment='#')
		for MODEL in MODELS:
			MODEL = MODEL.strip()
			if MODEL[0]=='#':
				# print("%s is skipped."%(MODEL[1:]))
				continue
			a_model_path = os.path.join(self.output_path,MODEL)
			round2_path = os.path.join(a_model_path,"round2")
			GROUP=None
			print("========== Now cleaning PARAMETERS for MODEL %s"%(MODEL))
			for ind, GROUP in GROUPS.iterrows():
				r2_group_path =os.path.join(round2_path,GROUP['group'])
				clean_params(delete_choice,MODEL,GROUP['group'],r2_group_path,GROUP['nframe'])

########### INSTRUCTIONS ###########

note0 = '''
##########################################################
CONSENSUS MODE                                           |
----------------------------------------------------------
Do you want to use CONSENSUS mode:

	0. NO  : ROUND 2 will run with DIFFERENT parameters
	1. YES : ROUND 2 will run with SAME parameters
----------------------------------------------------------
##########################################################
'''

note1_normal = '''
#######################################################
THIS PROGRAM IS FOR RUNNING ROUND 1                   |
-------------------------------------------------------
Select the number to run:

	1. Preparation directories
	2. Submit JOBs
	3. Exit
-------------------------------------------------------
#######################################################
'''
note1_consensus = '''
#######################################################
THIS PROGRAM IS FOR ROUND 1 IN CONSENSUS MODE         |
-------------------------------------------------------
Select the number to run:

	1. Preparation directories
	2. Submit JOBs
	3. Exit
-------------------------------------------------------
#######################################################
'''

note2_consensus= '''
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
'''

note2_nonconsensus= '''
#######################################################
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
'''

note2_normal= '''
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
'''

note3= '''
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
'''

########### USER INPUT ###########
if  __name__ == "__main__":
	parser = argparse.ArgumentParser(description="""
	# Let us create a user contact.""")
	parser.add_argument("-mp", help="Path to models")
	parser.add_argument("-ml", help="List of all models")
	parser.add_argument("-gl", help="List of groups")
	parser.add_argument("-param", help="Path to parameters")
	parser.add_argument("-pp", help="FULL Path to particles")
	parser.add_argument("-op", help="Output Path")

	args = parser.parse_args()

	mp_v = args.mp
	ml_v = args.ml
	gl_v = args.gl
	param_v = args.param
	particle_v = args.pp
	op_v= args.op

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
final_choice = 0
while final_choice <5:
	consensus = input(note0+"\n")
	if consensus =='0':
		print("========== YOU CHOSE NORMAL MODE!!\n")
		job1 = NORMAL_MODE_ROUND1(mp_v,ml_v,gl_v,param_v,particle_v,op_v)
		job2 = NORMAL_MODE_ROUND2(mp_v,ml_v,gl_v,param_v,particle_v,op_v)

		choose_round = input("Please choose the ROUND (1 or 2):\n")
		if choose_round =='1':
			options = input(note1_normal+"\n")
			if options =='1':
				model = job1.PREP()
			elif options =='2':
				job1.RUN()
			elif options=='3':
				final_choice=5
				print("Program exited.")
		else:
			options=input(note2_normal+"\n")
			if options=="1":
				print("\nPREPPING for ROUND2.\n")
				job2.PREP()
			elif options=="2":
				print("\nBATCH submission for ROUND2.\n")
				job2.RUN()
			elif options=="3":
				print("\nPOST-PROCESSING OUTPUTS!!\n")
				MODEL_PROCESSED = job2.CLEAN()
				print("\n%s is CLEANED.\n"%(MODEL_PROCESSED))
			elif options=="4":
				print("\nCLEANING UP YOUR MESS NOW!\n")
				MODEL_PROCESSED = job2.CLEAN_PARAMS()
				print("\n%s is CLEANED.\n"%(MODEL_PROCESSED))
			elif options=="5":
				final_choice=5
				print("Program exited.")
	else:
		print("========== YOU CHOSE CONSENSUS MODE!!\n")
		job1 = CONSENSUS_MODE_ROUND_1(mp_v,ml_v,gl_v,param_v,particle_v,op_v)
		job2 = CONSENSUS_MODE_ROUND_2(mp_v,ml_v,gl_v,param_v,particle_v,op_v)
		create_consensus = input("Do you want to create CONSENSUS directory? (0: No, 1:Yes)?\n")

		if create_consensus=='0':
			print("========== ONLY RUN ROUND 2 for non-CONSENSUS MODELS") 
			options=input(note2_nonconsensus+"\n")
			if options=="1":
				print("\nPREPPING for ROUND2.\n")
				job2.PREP_NONCONSENSUS()
			elif options=="2":
				print("\nBATCH submission for ROUND2.\n")
				job2.RUN_NONCONSENSUS()
			elif options=="3":
				print("\nPOST-PROCESSING OUTPUTS!\n")
				job2.CLEAN_OUTPUT_NONCONSENSUS()
			elif options=="4":
				job2.CLEAN_PARAMS()
			elif options=="5":
				final_choice=5
				print("Program exited.")
		else:
			print("========== MAKING CONSENSUS DIRECTORY!")
			choose_round = input("Please choose the ROUND (1) or (2) or (3) for both rounds:\n")
			if choose_round =='1':
				options = input(note1_consensus+"\n")
				if options =='1':
					job1.PREP()
				elif options =='2':
					job1.RUN()
				elif options=='3':
					print("Program exited.")
					final_choice=5
			elif choose_round=='2':
				options=input(note2_consensus+"\n")
				if options=="1":
					print("\nPREPPING for CONSENSUS.\n")
					job2.PREP_CONSENSUS()
				elif options=="2":
					print("\nBATCH submission for CONSENSUS.\n")
					job2.RUN_CONSENSUS()
				elif options=="3":
					print("\nPOST-PROCESSING OUTPUTS!\n")
					job2.CLEAN_OUTPUT_CONSENSUS()
				elif options=="4":
					job2.CLEAN_PARAMS()
				elif options=="5":
					final_choice=5
					print("Program exited.")
			elif choose_round=='3':
				options=input(note3+"\n")
				if options=="1":
					print("\n========== PREPPING for CONSENSUS ROUND 1 & 2.\n")
					job1.PREP_NONCONSENSUS()
					job2.PREP_CONSENSUS()
				elif options=="2":
					print("\n========== BATCH submission for CONSENSUS ROUND 1 & 2.\n")
					job1.RUN_NONCONSENSUS()
					job2.RUN_CONSENSUS()
				elif options=="3":
					print("\n========== POST-PROCESSING OUTPUTS!\n")
					job1.CLEAN_OUTPUT_NONCONSENSUS()
					job2.CLEAN_OUTPUT_CONSENSUS()
				elif options=="4":
					print("\n========== CLEANING UP YOUR MESS NOW!\n")
					job1.CLEAN_PARAMS()
					job2.CLEAN_PARAMS()
				elif options=="5":
					print("Program exited.")
					final_choice=5
else:
	exit
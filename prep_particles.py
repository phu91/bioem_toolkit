import sys
#sys.path.append('/mnt/home/pcossio/AnalysisPilar/ONECONF/lib/python3.7/site-packages/')

import mrcfile as mrc
import numpy as np
import argparse

if  __name__ == "__main__":
	parser = argparse.ArgumentParser(description="""
	Let us create a user contact.""")
	parser.add_argument("--input" , help="Name of the MRC stack")
	parser.add_argument("--opath" , help="Output Path")
	parser.add_argument("--output", help="Output Name")
	parser.add_argument("--start" , help="Start Image")
	parser.add_argument("--end"   , help="End Image")
	parser.add_argument("--method", help="Extract as SINGLE (0) or WHOLE stack (1)")
	args = parser.parse_args()

	input_v = args.input
	opath_v = args.opath
	output_v = args.output
	start_v = args.start
	end_v = args.end
	method_v = args.method
	print("==========================")
	print("Input MRC    : " + input_v)
	print("Output Path  : " + opath_v)
	print("Output Name  : " + output_v)
	print("Start Image  : " + start_v)
	print("End frames : " + end_v)
	if method_v=='1':
		print("Extract as  : SINGLE IMAGE" )
	elif method_v=='0':
		print("Extract as  : WHOLE STACK")
	elif method_v<'0' or method_v>'1':
		raise Exception("Invalid method! Choose 1 (SINGLE) or 0 (WHOLE stack)")
	print("==========================")

class extract_images:
	"""A simple example class"""
	def __init__(self,mrcFile,outpath,output,starting: int,ending: int,method):
		self.mrcFile = mrcFile
		self.outpath = outpath
		self.output = output
		self.starting = starting
		self.ending = ending
		self.method = method

	def extract_now(self):
		dataall = mrc.mmap(self.mrcFile,permissive='True')
		datacut = dataall.data[:,:][int(self.starting):int(self.ending)]
		nframe_tot = len(dataall.data[:,:])
		nframe_cut = len(datacut)
		print("\n++++++ There are %s FRAMEs in %s and %s FRAMEs are selected\n"%(nframe_tot,self.mrcFile,nframe_cut))
		if method_v=="0":
			mrc.write(opath_v+output_v, datacut,overwrite='True')
		if method_v=="1":
			for i in range(nframe_cut):
				start_name = int(self.starting)+i
				mrc.write((opath_v+"/particle_%s.mrc"%(start_name)), datacut[i],overwrite='True')
				print("frame %s"%(start_name))

job1 = extract_images(input_v, opath_v, output_v, start_v, end_v, method_v,)
job1.extract_now()


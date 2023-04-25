# bioem_toolkit
A set of scripts by Phu Tang and Miro Astore to run BIOEM on large experimental and synthetic datasets.
This toolkit takes in a processed particle stack and a set of molecular models and runs the bioEM algorithm, to determine the posterior probability that a given moleculr model corresponds to a given particle image. 

bioEM is run in two rounds.
Round 1 is a simple uniform sampling, to determine the angles in 3D space. Typically we search through 300 orientations in round 1 for each model and each particle. 
Round 2 is a more comprehensive search. We extract the best orientations calculated from each model in round 1and compare them, to generate a better estimate for the orientation.

With the posterior probabilities calculted by bioEM, one can move on to estimate the free energy landscape captured by the particle stack using cryoBIFE and cryoRE. For more information, see the bioEM documentation https://bioem.readthedocs.io/en/latest/. 

## RUN COMMAND
For details: 


`python bioem_toolkit.py -h`

Please be advised!!
At this moment BIOEM is currently not optimized to run on large MRCS file. 

Requirements: 
   numpy
   mrcfile https://pypi.org/project/mrcfile/
   bioEM version >=  2.1  https://github.com/bio-phys/bioem
   disBatch https://github.com/flatironinstitute/disBatch


#TODO
# 1. Rewrite bioEM to be able to read .mrcs particle stacks so particles do not need to be split into individual .mrc image files. This should be easy as .mrcs files are very regularly formatted. 
# 2. Rewrite bioEM to read .star files, so large numbers of Param files do not need to be written. These files should contain all the script needs to know about CTF parameters, and further more could contain the extra parameters that bioEM demands in additional columns..
# 3. Allow user specification of parameter and launch template files. 


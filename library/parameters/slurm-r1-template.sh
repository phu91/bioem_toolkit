#!/bin/bash -l

# Standard output and error:
# Initial working directory:
# Job Name:
#SBATCH -J r1-WhatModel
# Queue (Partition):
#SBATCH --constraint=rome
#SBATCH --partition=WhatPartition
# Request 1 node(s)
#SBATCH --nodes=1
# Set the number of tasks per node (=MPI ranks)
#SBATCH --ntasks-per-node=16
# Set the number of threads per rank (=OpenMP threads)
#SBATCH --cpus-per-task=8

# Wall clock limit:
#SBATCH --time=48:00:00

module load openmpi/4.0.7

#export KMP_AFFINITY=compact,granularity=core,1
export OMP_STACKSIZE=120M
export OMP_NUM_THREADS=8
export GPU=0
export BIOEM_DEBUG_OUTPUT=0
export BIOEM_ALGO=2

mpirun --map-by socket:pe=$OMP_NUM_THREADS -np 16 /mnt/home/pcossio/BenchmarkBioEM/BioEM_Mod_Gera/bioEM --Modelfile WhereModel/WhatModel.txt --Particlesfile WhereParticle --ReadMRC --Inputfile ../Param_BioEM_ABC --ReadOrientation ../Quat_36864

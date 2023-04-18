module load modules/2.0-20220630  gcc/11.2.0 openmpi/4.0.7 boost/1.78.0

pnum=$1
gname=$2
mod=$3

export OMP_NUM_THREADS=1
export GPU=0
export BIOEM_DEBUG_OUTPUT=1
export BIOEM_ALGO=2
unset SLURM_JOBID
export SLURM_JOB_NAME=WhatModel-R2
export WhereRound2CM=WhereRound2CM
export WhereParticles=WhereParticles
export WhereModel=WhereModel
export WhereOutput=WhereOutput
export WhereProject=WhereProject
export WhereRound1_CONSENSUS_Results=WhereRound1_CONSENSUS_Results

#cd $WhereProject

mpirun --bind-to none -np 1 /mnt/home/pcossio/BenchmarkBioEM/BioEM_Mod_Gera/bioEM  --Modelfile ${WhereModel}/${mod}  --Particlesfile ${WhereParticles}/${gname}/particle_${pnum}.mrc --ReadMRC --ReadOrientation $WhereRound1_CONSENSUS_Results/orientations/ANG_for-R2-${pnum} --Inputfile $WhereRound1_CONSENSUS_Results/parameters/Parm_${pnum} --OutputFile ../outputs/out-$pnum

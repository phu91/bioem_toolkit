module load modules/2.0-20220630  gcc/11.2.0 openmpi/4.0.7 boost/1.78.0

pnum=$1
gname=$2
mod=$3
unset SLURM_JOBID

export OMP_NUM_THREADS=1
export GPU=0
export BIOEM_DEBUG_OUTPUT=1
export BIOEM_ALGO=2
export SLURM_JOB_NAME=WhatModel-R2
export WhereRound2CM=WhereRound2CM
export WhereParticles=WhereParticles
export WhereModel=WhereModel
export WhereOutput=WhereOutput
export WhereProject=WhereProject
export WhereOrientation=WhereOrientation
export WhereParm=WhereParm

mpirun --bind-to none -np 1 /mnt/home/pcossio/BenchmarkBioEM/BioEM_Mod_Gera/bioEM  --Modelfile ${WhereModel}/${mod}.txt  --Particlesfile ${WhereParticles}/${gname}/particle_${pnum}.mrc --ReadMRC --ReadOrientation ${WhereOrientation}/ANG_R2_${pnum} --Inputfile ${WhereParm}/Parm_${pnum} --OutputFile ${WhereOutput}/out-$pnum

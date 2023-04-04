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
export WhereRound2=WhereRound2
export WhereParticles=WhereParticles
export WhereModel=WhereModel

mpirun --bind-to none -np 1 /mnt/home/pcossio/BenchmarkBioEM/BioEM_Mod_Gera/bioEM  --Modelfile ${WhereModel}/${mod}.txt  --Particlesfile ${WhereParticles}/${gname}/particle_${pnum}.mrc --ReadMRC --ReadOrientation ${WhereRound2}/${gname}/orientations/ANG_for-R2-${pnum} --Inputfile ${WhereRound2}/${gname}/parameters/Parm_${pnum} --OutputFile ${WhereRound2}/${gname}/outputs/out-$pnum
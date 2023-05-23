# BioEM Toolkit

BioEM Toolkit is a collection of tools that assist the run of BioEM on large experimental and synthetic datasets. This toolkit takes in a processed particle stack and a set of molecular models and runs the bioEM algorithm to determine the posterior probability that a given molecular model corresponds to a given particle image.

BioEM is run in two rounds. Round 1 is a simple uniform sampling to determine the angles in 3D space. Typically we search through 300 orientations in round 1 for each model and each particle. Round 2 is a more comprehensive search. We extract the best orientations calculated from each model in round 1 and compare them to generate a better estimate for the orientation. With the posterior probabilities calculated by bioEM, one can move on to estimate the free energy landscape captured by the particle stack using cryoBIFE and cryoRE. 

For more information, see the bioEM documentation `https://bioem.readthedocs.io/en/latest/`.


```bash
git clone git@github.com:phu91/bioem_toolkit.git
```

## Prerequisite
BioEM Installation
Visit `Visit https://github.com/bio-phys/BioEM` for installation instruction

```bash
git clone git@github.com:bio-phys/BioEM.git
```
A conda environment is suggested to be setup before running the toolkit
```bash
conda env create -f environment.yml
```
disBatch is also required to launch ROUND 2
```bash
git clone git@github.com:flatironinstitute/disBatch.git
```

## Preparation

### Preparing particles
Particles must be in a stacked MRCS format for ROUND 1. Individual MRC file for each particles are required for ROUND 2. The naming scheme should be `particle_`

#### Suggestion
Individual particles (`particle_0.mrc`, `particle_1.mrc`, etc.) should be stored in a sub-group directory, such as `particless/0-5k` (from particle 0 to particle 5000), and the stacked MRCS `particles_0-5k.mrcs` should be stored in `particles/`.

#### Tools
In `tools/prep_particles.py`, you can execute this Python script to extract stacked or individual particles. 
```bash
python prep_particles.py [-h] [--input INPUT] [--opath OPATH] [--output OUTPUT] [--start START] [--end END] [--method METHOD]
``` 

### Preparing models
Models must be in TXT format. 

#### Tools
`tools/prep_models_step1.tcl` is a TCL script that works in VMD to extract the PDB. Assumed VMD is installed. Remember to adjust the I/O accordingly to your `PDB` and `TRAJECTORY`. 

```bash 
vmd -e prep_models_step1.tcl
```
After extracting PDB files, run this script in `tools/prep_models_step1.sh` to convert `PDB` to `TXT` format. Notes: The charges and electrons are fixed to default values. 
```bash
./prep_models_step2.sh
``` 

## Warning:
**ALWAYS CHECK** the parameter files in `library/parameters` such as `Param_BioEM_template` or any slurm submission scripts before running bioem_toolkit.

`MODEL_LIST` and ` GROUP_LIST` can be found in the `test/`. BioEM is very delicate and serious about file handling, **PLEASE DO NOT CHANGE** anything if you are not sure about its functions because these small changes (etc., names) can cause BioEM to haul. 

## Usage
`run_dry` provides the running command to activate the interactive mode of the BioEM toolkit for `FIRST TIME` users. A command-line mode is activated with the flag `-cmd`. Notes: It is recommended to use a full (absolute) path format.  

A template for `MODEL_LIST` and ` GROUP_LIST` can be found in `test/`.

**To run the bioem_toolkit, one would simply execute the `run_dry` file. Make sure that you change all the paths accordingly to your machine:** 

```bash
./run_dry
```

### Required arguments:
**-mp**: Absolute path to where models are stored.

**-ml**: Text file with a list of all models.

**-gl**: List of groups which particles are organised into. Eg. 0-10k 0-10k.mrcs 10000

**-param**: Absolute path to parameters files which this script uses. Usually stored in the github repo in 'bioem_toolkit/library/parameters'.

**-pp**: Absolute path of directory where particle .mrcs files are stored.

**-op**: Directory where output will be stored.

### A more elaborated help menu is activated as:
```bash 
python bioem_toolkit/bioem_toolkit.py -h
```

### bioem_toolkit: Current parameters




# **Current development:**


## Contributing

Pull requests are welcome. For significant changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
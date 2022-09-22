# Data Management
#### Kat Nykiel and Panos Manganaris

## fireworks details
1. how can you monitor VASP convergence through fireworks?
   what are the monitoring capabilities?
   - error detection?
   - convergence detection?
2. how can you read error/warnings printed in VASP.std_out?
3. how can each scientist use their own scratch/queue resources?

## TODO linking to raw data folders
checking raw data is sometimes necessary.

1. make it easy to navigate to run folder with database unique ID.

## Easy Metadata
Jobflow jobs can be defined with an additional metadata attribute.

The metadata will be stored alongside the job outputs making it easier to query.

### for professor Arun
For instance we can write an automated metadata dictionary including
- execution date
- level of theory
- size of supercell
- type of defect
- mix
- associated literature citations
- etc

Of course, the calculators for many of these qualities already exist
and can simply be called on the formula of runs without saved
metadata, but storing this might be more convenient if technically
less correct.

Either way, This will make it very easy to write mongo queries that
retrieve the data we need for our various ML analysis projects and
makes checking outlier predictions very easy. Including checking for
potential mistakes in data retrieved from literature.

## minimum growing pains
assembling predefined workflows into an experimental batch is pretty
easy and can be done by anyone with basic knowledge of python
scripting.

Creating workflows from scratch does require some python development
knowledge, however this can task can be made collaborative with good
git practice and published as a package of predefined workflows for
non-developer users.

Finally, if someone insists on running experiments the old-fashioned
way, it is easy to parse the results manually and upload all details
to the centralized database.

The only missing piece is the necessary database host and disk space
on Purdue's Geddes Containerized Workloads Cluster.

### PROOF OF CONCEPT on Mongo DB Atlas


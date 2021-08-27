# IBM cloud route table switcher

## Introduction

This Python script can be used to build an automated switching feature to reroute traffic if a connection goes down

## Installation and Use

1. The environment used to run the script requires the **python3** package to be installed
2. Download the two files to a directory on the server
3. edit the **config.yaml** file to include the Cloud Access API key along with the VPC to be processed and the table pairs.
4. Ensure the **switch-tables.py** file is executable (Linux mode 755)
5. Run the command **./switch-tables.py**

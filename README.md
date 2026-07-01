# chime-reduction

The CHIME data transfer method is fully automated with cron jobs now. 

One job runs on prospero and pulls the data from the remote sftp server with the following command:

    15 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; sftp -P 2022 dbautist@192.33.116.19:numpy_files/*$(date +\%Y-\%m-\%d)*npy . ; source /opt/local/etc/profile.d/conda.sh; conda activate rfi ; python3 chime/make_waterfalls.py | mail -s "CHIME data transfer waterfall plots" dbautist

This script runs at 5:15 am each morning and pulls the most recent data from the server to the home directory `/users/dbautist/CHIME_landing_directory/`. It does this by searching for the current date in the filenames and pulls only that data. 

It then runs a python script to populate them in their own directories for each date of obervation and generates a waterfall plot to summarize the data. Afterwards it sents me an email with the outputs of make_waterfalls.py

A second job runs on prospero and reduces the data with the following command:

    20 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; source /opt/local/etc/profile.d/conda.sh; conda activate rfi ; python3 chime/gui_reduction.py -o /home/scratch/dbautist/TEST/410/ -l /users/dbautist/CHIME_landing_directory/calibration_log.csv | mail -s "CHIME data transfer gui reduction ARCHIVE" -a /home/scratch/dbautist/TEST/410/plots/debug.png dbautist

This script runs at 5:20 am each morning and reduces the data to a volume that is manageable by the [DRIFT](https://drift.nrao.edu) data ingestion algorithm. 

This job runs again, this time moving the data to a staging directory where it will live until it gets sent to DRIFT ingestion. This second execution is performed with the following command: 

    25 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; source /opt/local/etc/profile.d/conda.sh; conda activate rfi ; python3 chime/gui_reduction.py -noplot -o /users/dbautist/CHIME_landing_directory/csvStaging/ -l /users/dbautist/CHIME_landing_directory/csvStaging/drift_transfer.log | mail -s "CHIME data transfer DRIFT reduction" dbautist

A third job runs on `cvpost-master-2` and moves the data to the lustre workspace with the following command:

    30 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; python3 chime/move_data.py | mail -s "CHIME data transfer to lustre" dbautist

This script runs every morning at 5:30 am moves the data from `CHIME_landing_directory` to `/lustre/cv/projects/ESM/CHIME_data`. Afterwards it sends me an email with the outputs of move_data.py

## Installation

Clone this repository to your local machine

    git clone https://github.com/dbautista98/chime-reduction.git

Navigate into this newly cloned repository:

    cd chime-reduction

Use [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html) to create a python environment and install the necessary packages. If installing on GBO data reduction machines, there is an additional step of enabling conda before you can create the environment. 

    conda env create --file environment.yml

Activate this new conda environment

    conda activate chime

Install this repository to your environment. If you plan to edit this code and have your changes, pip install this package with the `--editable` flag. Otherwise pip install with no special flags:

    pip install --editable .

OR 

    pip install .

At this point you should be able to activate the conda environment and run the python files from this repository.

This can be confirmed by running 

    check_installation.py

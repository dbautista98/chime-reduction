# chime-reduction

The CHIME data transfer method is fully automated with cron jobs now. 

One job runs on prospero and pulls the data from the remote sftp server with the following command:

    15 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; sftp -P 2022 dbautist@192.33.116.19:numpy_files/*$(date +\%Y-\%m-\%d)*npy . ; source /opt/local/etc/profile.d/conda.sh; conda activate rfi ; python3 make_waterfalls.py | mail -s "CHIME data transfer waterfall plots" dbautist

This script runs at 5:15 am each morning and pulls the most recent data from the server to the home directory `/users/dbautist/CHIME_landing_directory/`. It does this by searching for the current date in the filenames and pulls only that data. 

It then runs a python script to populate them in their own directories for each date of obervation and generates a waterfall plot to summarize the data. Afterwards it sents me an email with the outputs of make_waterfalls.py

A second job runs on prospero and reduces the data with the following command:

    20 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; source /opt/local/etc/profile.d/conda.sh; conda activate rfi ; python3 gui_reduction.py | mail -s "CHIME data transfer gui reduction" -a /home/scratch/dbautist/TEST/610/plots/debug.png dbautist

This script runs at 5:20 am each morning and reduces the data to a volume that is manageable by the gbt-rfi-gui data ingestion algorithm. 

A third job runs on cvpost-master and moves the data to the lustre workspace with the following command:

    30 5 * * *  cd /users/dbautist/CHIME_landing_directory/ ; python3 move_data.py | mail -s "CHIME data transfer to lustre" dbautist

This script runs every morning at 5:30 am moves the data from `CHIME_landing_directory` to `/lustre/cv/projects/ESM/CHIME_data`. Afterwards it sends me an email with the outputs of move_data.py

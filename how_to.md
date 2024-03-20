# how to transfer CHIME data

The CHIME data transfer method is fully automated with cron jobs now. 

One job runs on prospero and pulls the data from the remote sftp server with the following command:

    0 1 * * *  cd /users/dbautist/CHIME_landing_directory/ ; sftp -P 2022 dbautist@192.33.116.19:numpy_files/*$(date +\%Y-\%m-\%d)*npy .

This script runs at 1am each morning and pulls the most recent data from the server to the home directory `/users/dbautist/CHIME_landing_directory/`. It does this by searching for the current date in the filenames and pulls only that data. 

The second job runs on cvpost-master and moves the data to the lustre workspace with the following command:

    0 2 * * *  cd /users/dbautist/CHIME_landing_directory/ ; python3 move_files.py | mail -s "CHIME data transfer" dbautist

This script moves the data from `CHIME_landing_directory` to `/lustre/cv/projects/ESM/CHIME_data` and populates them in their own directories. Afterwards it sends me an email with the outputs of move_files.py

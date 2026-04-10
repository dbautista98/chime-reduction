import os
import socket
from datetime import datetime

# CHIME package imports
try:
    from . import util
except:
    import util

DEVELOPMENT = False
testing = True

def get_dates(target_directory):
    f = []
    for (dirpath, dirnames, filenames) in os.walk(target_directory):
        f.extend(filenames)
        break
    date_list = dirnames
    return date_list

def move_data(input_directory, output_directory, move_method="cp", development=True):
    # file wrangling commands
    file_grab = f"{input_directory}/*/*.csv"
    command = f"{move_method} {file_grab} {output_directory}"
    file_ls = f"ls {file_grab}"

    # debug prints 
    print("found files:")
    print(file_ls)
    os.system(file_ls)

    print()
    print("moving files:")
    print(command)

    # actually move files
    if not development:
        os.system(command)
        
        print()
        print("new file location(s):")
        print(f"ls {output_directory}/*csv")
        os.system(f"ls {output_directory}/*csv")
        update_transfer_log(input_directory, output_directory, log_file_dir=input_directory)
    return 

def update_transfer_log(output_directory, data_destination, log_file_dir='./'):
    log_file_name = "drift_transfer.log"
    outfile = f"{log_file_dir}/{log_file_name}"
    today = datetime.today().strftime('%Y-%m-%d')

    # get list of dates 
    date_list = get_dates(output_directory)

    # check if log file exists
    if not os.path.exists(outfile):
        header = "date,data_date-YMD,transfer_date,transfer_location,success\n"
        with open(outfile, "w") as f:
            f.write(header)

    # populate line for newly transferred data
    new_lines = ""
    for this_date in date_list:
        new_lines += f"{this_date},{util.yyyy_ddd_to_Y_m_d(this_date)},{today},{data_destination},True\n"

    # update the log file 
        with open(outfile, 'a') as f:
            f.write(new_lines)

    print(f"\nlogfile updated at: {outfile}")
    return 

def drift_transfer_driver(host_name):
    production = ["gygax"]
    test = ["hypatia", "prospero", "newton", "planck"]

    print(f"running on {host_name}\n")

    if host_name in production:
        input_directory = "/users/dbautist/CHIME_landing_directory/csvStaging/"
        output_directory_TEST = "/home/drift-upload-test/"
        output_directory_PROD = "/home/drift-upload/"
        move_method = "cp"
        move_data(input_directory, output_directory_TEST, move_method, development=DEVELOPMENT)
        move_data(input_directory, output_directory_PROD, move_method, development=DEVELOPMENT)

        if not DEVELOPMENT:
            # remove the empty temp directories from staging 
            temp_directories = get_dates(input_directory)
            for dir in temp_directories:
                print(f"removing {input_directory}/{dir}")
                # os.rmdir(f"{input_directory}/{dir}") # the directories are no longer empty with just a copy command 
                os.system(f"rm -rf {input_directory}/{dir}") # this will be reverted back once deployed only on production 

        return True

    elif host_name in test:
        input_directory = "/users/dbautist/CHIME_landing_directory/csvStaging/"
        output_directory= "/home/scratch/dbautist/TEST/should_be_empty/"
        move_method = "cp"
        move_data(input_directory, output_directory, move_method, development=(not test))
        return True
    
    else:
        print("not running on a valid machine:")
        print(host_name)
        return False



if __name__ == "__main__":
    print()
    print("starting DRIFT transfer")

    host_device = socket.gethostname()
    execution = drift_transfer_driver(host_device)

    if execution:
        print()
        print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")
    else: 
        print()
        print("Job not executed")

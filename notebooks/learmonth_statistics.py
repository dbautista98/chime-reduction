import numpy as np
import matplotlib.pyplot as plt
from calibration import *
import pandas as pd
from tqdm import trange
import os

outdir = "/users/dbautist/CHIME_landing_directory/learmonthData/summary_plots/"
data_dir = "/home/scratch/dbautist/learmonth_data/"
summary_path = f"{outdir}/summary_fluxes.csv"

months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
years = ['24', '25']
month_dict = {}
for year in years:
    for month in months:
        search_string = ""
        month_dict[year+month] = glob.glob(f"{data_dir}/*{year}{month}*SRD")

def get_day_number(filepath):
    date_str = os.path.basename(filepath)[1:-4]
    time_UTC = datetime.strptime(date_str, "%y%m%d")
    return int(time_UTC.strftime("%j"))

def get_day(path):
    filename = os.path.basename(path).replace(".SRD", "")
    YYMMDD = filename[1:]
    datetime_obj = datetime.strptime(YYMMDD, "%y%m%d")
    return datetime_obj

def loop_bool(df):
    check_median = (not np.isnan(np.nanmedian(df["410"]))) and np.nanmedian(df["410"]) != 0 and np.nanmedian(df["410"]) != 1 and np.nanmedian(df["410"]) > 0
    result  = check_median
    return result

tolerance = 10
n_hours = 4
sec_per_hr = 3600

if os.path.exists(summary_path):
    summary_df = pd.read_csv(summary_path)
    for i in range(len(summary_df)):
        summary_df.loc[i, "date"] = datetime.strptime(summary_df.iloc[i]["date"], "%Y-%m-%d")
else:
    sufficient_data = []
    insufficient_data = []
    good_data = []
    data_paths = []

    days = []
    flux_410 = []
    flux_610 = []
    for year in years:
        for month in months:
            print(f"year: {year}\nmonth: {month}")
            for i in trange(len(month_dict[year+month])):
                this_path = month_dict[year+month][i]
                data_paths.append(this_path)
                df = load_Learmonth_data(this_path)
                if loop_bool(df):
                    sufficient_data.append(this_path)
                    good_data.append(True)
                else:
                    insufficient_data.append(this_path)
                    good_data.append(False)
                flux_410.append(np.nanmedian(df["410"]))
                flux_610.append(np.nanmedian(df["610"]))
                days.append(get_day(this_path))

    data_dict = {"date":days, "path":data_paths, "flux_410":flux_410, "flux_610":flux_610, "good_data":good_data}
    summary_df = pd.DataFrame(data_dict)
    summary_df.to_csv(summary_path, index=False)

# check against columns in df
print("data quality check")
print("good:", len(summary_df[summary_df["good_data"] == True]), "bad:", len(summary_df[summary_df["good_data"] == False]))

good_flux_df = summary_df[summary_df["good_data"] == True]

plt.figure()
plt.scatter(good_flux_df["date"], good_flux_df["flux_410"], s=1)
plt.ylim(10, 150)
plt.grid()
plt.title("Learmonth median solar flux at 410 MHz")
plt.ylabel("Flux [SFU]")
plt.savefig(f"{outdir}/410.png", bbox_inches="tight", transparent=False)
plt.close()

plt.figure()
plt.scatter(good_flux_df["date"], good_flux_df["flux_610"], s=1)
plt.ylim(10, 150)
plt.grid()
plt.title("Learmonth median solar flux at 610 MHz")
plt.ylabel("Flux [SFU]")
plt.savefig(f"{outdir}/610.png", bbox_inches="tight", transparent=False)
plt.close()

solar_flare_date = datetime.strptime("2024_130", "%Y_%j")

plt.figure(figsize=(10, 6))
plt.scatter(good_flux_df["date"], good_flux_df["flux_410"], label="410 MHz", s=5)
plt.scatter(good_flux_df["date"], good_flux_df["flux_610"], label="610 MHz", s=5)
plt.title("Median solar flux")
plt.ylabel("flux [SFU]")
plt.xlabel("day of 2024")
plt.grid()
plt.hlines(np.median(good_flux_df["flux_410"]), min(good_flux_df["date"]), max(good_flux_df["date"]), label=f"median 410 MHz = {np.median(good_flux_df["flux_410"])} +- %s"%np.round(np.std(good_flux_df["flux_410"]), 2))
plt.hlines(np.median(good_flux_df["flux_610"]), min(good_flux_df["date"]), max(good_flux_df["date"]), color='orange', label=f"median 610 MHz = {np.median(good_flux_df["flux_610"])} +- %s"%np.round(np.std(good_flux_df["flux_610"]), 2))
plt.vlines(solar_flare_date, 30, 110, label="solar flare event", color="red")
plt.legend()
plt.savefig(f"{outdir}/solar_flux.png", transparent=False, bbox_inches="tight")

# with open(f"{outdir}/good_data.txt", "w") as f:
#     for file in sufficient_data:
#         f.write(f"{file}\n")


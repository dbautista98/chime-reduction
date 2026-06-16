import glob
import os
from datetime import datetime, timezone, timedelta
import shutil
import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u

# plotly imports
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# CHIME package imports
try:
    from . import calibration
    from . import util
except:
    import calibration
    import util

# TODO: 
#  - what happens if time_zone=None goes into make_waterfalls?

def plot_waterfall(data_path, outdir="./", outtype="png", calibrated=False, time_zone=None):
    """
    This function reads in the CHIME data and uses it to generate and save a static waterfall 
    plot using matplotlib. It expects to be given the path to a directory containing the 
    corresponding .npy files. 

    Arguments:
    ---------------
    data_path : str
        The file path to the parent directory, as created by `make_waterfalls.move_files`
        The parent directory is the name of the date of observation, with the 
        format %Y_%j (eg: 2026_001 for January 1, 2026). An example path 
        is (/path/to/directory/2026_001)
    outdir : str
        The parent directory that the organized data can be found in. This function 
        generates the last directory level based on the file name. The default directory 
        is the current working directory. 
    outtype : str
        THe file type that the resulting waterfall plot will be saved as. The options 
        are {png, pdf}, and the default is to save as a png. 
    calibrated : bool
        A flag indicating whether to calibrate the data to Jy before generating the 
        waterfall plot. If the data is not calibrated, the data will have units of counts. 
        The default is to not calibrate the data.
    time_zone : datetime.timezone
        A datetime object indicating what timezone the data is in. The default is to 
        use UTC when generating the waterfall plot.
    """

    assert outtype in ["png", "pdf"], "outtype must be either png or pdf"
    CHIME_data, frequency, timestamps = calibration.load_CHIME_data(os.path.dirname(data_path))
    if calibrated:
        unit = "Jy"
        CHIME_data = calibration.calibration(data_path)
        vmin=1e4
        vmax=7e5
    else:
        unit = "counts"
        vmin=0
        vmax=4e7
    start_time = timestamps[0]
    end_time = timestamps[-1]

    time_series = np.sum(CHIME_data, axis=1)
    average_spectrum = np.mean(CHIME_data, axis=0)

    extent = [np.round(np.min(frequency)), np.round(np.max(frequency)), max(timestamps), min(timestamps)] 
    fig = plt.figure(figsize=(10,10))
    gs = fig.add_gridspec(2,2, hspace=0.02, wspace=0.03, width_ratios=[3,1], height_ratios=[1,3])
    (ax1, ax2), (ax3, ax4) = gs.subplots(sharex="col", sharey="row")
    ax1.set_title(f"GBO CHIME outrigger data\n{start_time.astimezone(time_zone).strftime('%Y-%m-%d %H:%M:%S %Z')} to {end_time.astimezone(time_zone).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    ax1.semilogy(frequency, average_spectrum, color="black", linewidth=1)
    ax1.set_ylabel(f"average power [{unit}]")
    ax2.set_visible(not ax2)
    ax3.imshow(CHIME_data, aspect="auto", extent=extent, vmin=vmin, vmax=vmax)
    ax3.set_xlabel("Frequency [MHz]")
    ax3.set_ylabel(f"{start_time.astimezone(time_zone).strftime('%Z')} time (mm-dd hh)")
    ax4.plot(time_series, timestamps, color="black", linewidth=1)
    ax4.set_xlabel(f"integrated power\n[{unit}]")
    plt.savefig(f"{outdir}/{start_time.strftime('%Y_%j')}_waterfall.{outtype}", bbox_inches="tight", transparent=False)
    print(f"saved plot to: {outdir}/{start_time.strftime('%Y_%j')}_waterfall.{outtype}")
    plt.close()

def plot_html(data_path, outdir="./", outtype="html", calibrated=False, time_zone=None):
    """
    This function reads in the CHIME data and uses it to generate and save an interactive 
    waterfall plot using plotly. It expects to be given the path to a directory containing the 
    corresponding .npy files. 

    A useful page for plotting with subplots:
    https://stackoverflow.com/questions/75871154/plotly-share-x-axis-for-subset-of-subplots

    Arguments:
    ---------------
    data_path : str
        The file path to the parent directory, as created by `make_waterfalls.move_files`
        The parent directory is the name of the date of observation, with the 
        format %Y_%j (eg: 2026_001 for January 1, 2026). An example path 
        is (/path/to/directory/2026_001)
    outdir : str
        The parent directory that the organized data can be found in. This function 
        generates the last directory level based on the file name. The default directory 
        is the current working directory. 
    outtype : str
        THe file type that the resulting waterfall plot will be saved as. The options 
        are {png, pdf}, and the default is to save as a png. 
    calibrated : bool
        A flag indicating whether to calibrate the data to Jy before generating the 
        waterfall plot. If the data is not calibrated, the data will have units of counts. 
        The default is to not calibrate the data.
    time_zone : datetime.timezone
        A datetime object indicating what timezone the data is in. The default is to 
        use UTC when generating the waterfall plot.
    """
    assert outtype in ["html"], "outtype must be html"
    CHIME_data, frequency, timestamps = calibration.load_CHIME_data(os.path.dirname(data_path))

    if calibrated:
        unit = "Jy"
        CHIME_data = calibration.calibration(data_path)
        vmin=1e4
        vmax=7e5
    else:
        unit = "counts"
        vmin=0
        vmax=4e7
    start_time = timestamps[0]
    end_time = timestamps[-1]

    pfig = px.imshow(
                CHIME_data,
                x = frequency,      # Frequency (must remove leading dimension)
                y = timestamps,                          # Time (datetime)
                # origin="upper",                 # matches Matplotlib invert_yaxis()
                aspect="auto",
                zmin=vmin,
                zmax=vmax,
                color_continuous_scale="Viridis",
            )

    pfig.update_layout(
        title=f"GBO CHIME outrigger data\n{start_time.astimezone(time_zone).strftime('%Y-%m-%d %H:%M:%S %Z')} to {end_time.astimezone(time_zone).strftime('%Y-%m-%d %H:%M:%S %Z')}",
        xaxis_title="Frequency (Hz)",
        yaxis_title=f"Time ({start_time.astimezone(time_zone).strftime('%Z')})",
        coloraxis_colorbar=dict(title=f"Magnitude ({unit})"),
    )
    pfig.update_xaxes(tickformat="~s")          # x-axis: engineering notation (like EngFormatter) e.g., 1k, 10M, etc.
    pfig.update_yaxes(tickformat="%H:%M")       # y-axis: datetime formatting (HH:MM)
    pfig.write_html(f"{outdir}/{start_time.strftime('%Y_%j')}_waterfall.{outtype}")  # Save to HTML
    print(f"saved plot to: {outdir}/{start_time.strftime('%Y_%j')}_waterfall.{outtype}")
    return 

def move_files(data_dir, outdir):
    """
    Organize the provided directory, moving all raw CHIME data (.npy files) into 
    directories named with the date that the data was taken (YYYY_DDD format). These
    directories are created according to the date data that is contained within the 
    file names and can be returned using `util.get_date(filepath)`

    Before running this function, there are many .npy files. 
    After running this function, the .npy files are contained in directories with 
    a naming convention of (YYYY_DDD)

    Example end result: 
        $ ls 
        2026_001/
        2026_002/
        2026_003/

    Arguments:
    ---------------
    data_dir : str
        The path to the directory containing the CHIME .npy files to organize. 
    outdir : str
        The location that the CHIME .npy files should be organized and moved to. 
    """
    print(f"searching for .npy files in {data_dir}")
    all_files = glob.glob(f"{data_dir}/*npy")
    if len(all_files) == 0:
        print("ERROR:: no data found")

    for file in all_files:
        this_date = util.get_date(file)
        topdir = outdir + "/" + this_date
        util.check_dir(topdir)
        outpath = topdir + "/" + os.path.basename(file)
        if os.path.exists(outpath):
            os.remove(file)
        else:
            print(f"moved {file} to {outpath}")
            shutil.move(file, outpath)

def make_waterfalls(outdir, outtype='png', calibrated=False, time_zone=None):
    """
    Searches for directories with the naming convention (YYYY_DDD), and generates 
    waterfall plots generated from the contents of the .npy files. These waterfall
    plots will be written into the directry with the corresponding date. 

    Arguments:
    ---------------
    outdir : str
        The location that the waterfall plots will be written to. These should be the
        same directory that the .npy files are stored in. 
    outtype : str
        THe file type that the resulting waterfall plot will be saved as. The options 
        are {png, pdf}, and the default is to save as a png. 
    calibrated : bool
        A flag indicating whether to calibrate the data to Jy before generating the 
        waterfall plot. If the data is not calibrated, the data will have units of counts. 
        The default is to not calibrate the data.
    time_zone : datetime.timezone
        A datetime object indicating what timezone the data is in. The default is to 
        use UTC when generating the waterfall plot.
    """
    assert outtype in ["png", "pdf"], "File type should be either png or pdf"

    dirs = glob.glob(f"{outdir}/202*/")
    try:
        dirs.remove("__pycache__/")
    except Exception:
        pass

    for dir in dirs:
        date = dir.split("/")[-2]
        if os.path.exists(f"{outdir}/{date}/{date.replace('/', '')}_waterfall.{outtype}"):
            pass
        else:
            contents = glob.glob(dir + "/*npy")
            contents.sort()
            plot_waterfall(dir, outdir=f"{outdir}/{date}", outtype=outtype, calibrated=calibrated, time_zone=time_zone)
            plot_html(dir, outdir=f"{outdir}/{date}", outtype="html", calibrated=calibrated, time_zone=time_zone)

if __name__ == "__main__":
    outtype = "png"
    calibrated = False
    time_zone = timezone.utc

    data_dir = os.getcwd()
    outdir = os.getcwd()

    move_files(data_dir, outdir)
    make_waterfalls(outdir, outtype=outtype, calibrated=calibrated, time_zone=time_zone)
    print(f"Job finished: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}")

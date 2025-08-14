# TODOs
- [ ] Change printed EXAMPLE msg
- [ ] Review/Change Notebook tutorials
- [X] Apply changes to --ssh case
- [X] Extract data based on version
- [X] Change db table to include Version of GPM DATA

# Precip

Python code to display precipitation globally using [GPM dataset](https://gpm.nasa.gov/data/visualizations/precip-apps).

Information on volcanoes is retrieved from [Global Volcanism Program](https://volcano.si.edu/) webservice.

# Installation
- Create destination folder from terminal and clone the repo:
```bash
cd $HOME
mkdir -p $HOME/code/Precip
git clone git@github.com:geodesymiami/Precip.git $HOME/code/Precip
```

- Set environment variables (temp):
```bash
export PRECIP_HOME=$HOME/code/Precip
export PRECIP_DIR=$SCRATCHDIR/gpm_data
```
- Prepend to your `$PATH`
```bash
export PATH=${PRECIP_HOME}/src/Precip/cli:$PATH
export PYTHONPATH=${PRECIP_HOME}/src:$PYTHONPATH
```
## Install requirements

### Create a new virtual environment (**Optional**)
Create a virtual env named `precipitation` with `conda`(recommended) or `python`: 
```bash
conda create -n precipitation #Choose your preferred name
```
Or
```bash
python -m venv precipitation #Choose your preferred name
```
---
### Install modules from requirements.txt file
If you have `conda`:
```bash
cd $PRECIP_HOME
conda install --yes -c conda-forge --file requirements.txt
```
Or if you don't:
```bash
cd $PRECIP_HOME
pip install -r requirements.txt
```

# Enable download of GPM data
In order to be able to download GPM data locally, you need to have an active **EarthData account**.

To create one, follow the steps below:
- [Create an EarthData account](https://wiki.earthdata.nasa.gov/display/EL/How+To+Register+For+an+EarthData+Login+Profile)
- [Link GES DISC with your account](https://disc.gsfc.nasa.gov/earthdata-login)
- [Generate Earthdata Prequisites Files](https://disc.gsfc.nasa.gov/information/howto?title=How%20to%20Generate%20Earthdata%20Prerequisite%20Files)

Otherwise you can use a mockup account, just copy paste the following code in your terminal ([Mac/Linux](#Mac/Linux), [Windows](#Windows)):

## Mac/Linux

### Create `.netrc` file
```bash
cd $HOME
touch .netrc
echo "machine urs.earthdata.nasa.gov login emrehavazli password 4302749" >> .netrc
chmod 0600 .netrc
```
### Create `.urs_cookies` file
```bash
touch $HOME/.urs_cookies
```
### Create `.dodsrc` file
```bash
touch $HOME/.dodsrc

echo "HTTP.NETRC=$HOME/.netrc" >> $HOME/.dodsrc
echo "HTTP.COOKIEJAR=$HOME/.urs_cookies" >> $HOME/.dodsrc
```

## Windows

### Create `.netrc` file
- Open Notepad
- Enter (without quotes):

machine urs.earthdata.nasa.gov login emrehavazli password 4302749

Save as C:\.netrc

### Create `.urs_cookies` file
From terminal (`Win` + **R**, type _cmd_ )

```bash
cd %USERPROFILE%
NUL > .urs_cookies
```
### Create `.dodsrc` file
```bash
cd %USERPROFILE%
NUL > .dodsrc
echo "HTTP.NETRC=%USERPROFILE%/.netrc" >> %USERPROFILE%\.dodsrc
echo "HTTP.COOKIEJAR=%USERPROFILE%/.urs_cookies" >> %USERPROFILE%\.dodsrc
```

# Examples
You can run the code through command line by simply runnig the following command:
```bash
plot_precipitation.py Merapi --style bar --period=20060101:20070101
```
This line will show the precipitation over **Merapi** volcano from **01 January 2006** to **2007** as a **bar** plot, with vertical lines representing the eruptions.

For more examples run:
```bash
plot_precipitation.py --h
```

If You want to show (almost) all the available types of plot in one single command, run:
```bash
run_plot_precipitation_all.py Merapi --period=20060101:20070101
```
You can add some of the arguments from `gplot_precipitation.py`, like:
- `--roll`
- `--bins`
- `--log`
- `--save`

For visual examples, refer to the following [Jupyter Notebook](Notebooks/Examples.ipynb).

# JetStream

If you have special access to our Cloud Service, you can try to connect to JetStream and use the data uploaded there instead of downloading them locally with `--use-ssh` argument.

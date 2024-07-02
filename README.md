# precip

Python code to display precipitation globally using [GPM dataset](https://gpm.nasa.gov/data/visualizations/precip-apps).

# Installation
- Create destination folder from terminal and clone the repo:
```
cd $HOME
mkdir ./code
mkdir ./code/precip
git clone git@github.com:geodesymiami/precip.git ./code/precip
```

- Set environment variables (temp):
```
export PRECIP_HOME=$HOME/code/precip
```
- Prepend to your `$PATH`
```
export PATH=${PRECIP_HOME}/src/precip/cli:$PATH
export PYTHONPATH=${PRECIP_HOME}/src:$PYTHONPATH
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
```
cd $HOME
touch .netrc
echo "machine urs.earthdata.nasa.gov login emrehavazli password 4302749" >> .netrc
chmod 0600 .netrc
```
### Create `.urs_cookies` file
```
touch $HOME/.urs_cookies
```
### Create `.dodsrc` file
```
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

```
cd %USERPROFILE%
NUL > .urs_cookies
```
### Create `.dodsrc` file
```
cd %USERPROFILE%
NUL > .dodsrc
echo "HTTP.NETRC=%USERPROFILE%/.netrc" >> %USERPROFILE%\.dodsrc
echo "HTTP.COOKIEJAR=%USERPROFILE%/.urs_cookies" >> %USERPROFILE%\.dodsrc
```

# Examples
You can run the code through command line by simply runnig the following command:
```
get_precipitation_lalo.py Merapi --style bar --period=20060101:20070101
```
This line will show the precipitation over **Merapi** volcano from **01 January 2006** to **2007** as a **bar** plot, with vertical lines representing the eruptions.

For more examples run:
```
get_precipitation_lalo.py --h
```

If You want to show all (almost) the available types of plot in one single command, run:
```
get_all.py Merapi --period=20060101:20070101
```
You can add some of the arguments from `get_precipitation_lalo.py`, like:
- `--roll`
- `bins`
- `log`
- `--save`

For visual examples, refer to the following [Jupyter Notebook](Examples.ipynb).

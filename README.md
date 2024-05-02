# precip

Python code to display precipitation data

# Installation

- Set environment varables (temp):
```
export PRECIP_HOME=~/code/precip
```
- Prepend to your $PATH
```
export PATH=${PRECIP_HOME}/src/precip/cli:$PATH
export PYTHONPATH=${PRECIP_HOME}/src:$PYTHONPATH
```

# Enable download of GPM data
- [Create an EarthData account](https://wiki.earthdata.nasa.gov/display/EL/How+To+Register+For+an+EarthData+Login+Profile)
- [Link GES DISC with your account](https://disc.gsfc.nasa.gov/earthdata-login)
- [Generate Earthdata Prequisites Files](https://disc.gsfc.nasa.gov/information/howto?title=How%20to%20Generate%20Earthdata%20Prerequisite%20Files)
"""
This file contains the configuration for the precip package.
"""

# workDir = 'WORKDIR'
# TODO remove this
WORKDIR = 'SCRATCHDIR'
SCRATCHDIR = 'SCRATCHDIR'
PRODDIR = 'PRECIP_PRODUCTS_DIR'
GPM_FOLDER = 'gpm_data'
JSON_DOWNLOAD_URL = 'https://webservices.volcano.si.edu/geoserver/GVP-VOTW/wms?service=WFS&version=1.0.0&request=GetFeature&typeName=GVP-VOTW:E3WebApp_Eruptions1960&outputFormat=application%2Fjson'
JSON_VOLCANO = 'volcanoes.json'
START_DATE = '20000601'

#End Date may vary, check on https://disc.gsfc.nasa.gov/datasets?keywords=%22IMERG%20Late%22&page=1
if True:
    END_DATE ='20240601' 
else:
    END_DATE = str(datetime.today().date() - relativedelta(days=1)).replace('-', '')
    
FINAL06 = '2021-09-30'
FINAL07 = '2024-01-31'
ELNINOS = {'weak nina': [[2000.4164, 2001.1233], [2005.8712, 2006.2], [2007.5342, 2008.4548], [2008.874, 2009.2], [2010.4521, 2011.3671], [2011.6192, 2012.2027], [2016.6219, 2016.9562], [2017.7863, 2018.2849], [2020.6219, 2021.2849], [2021.7041, 2023.0384]], 'moderate nina': [[2007.7041, 2008.2877], [2010.5342, 2011.1233], [2011.7863, 2011.9534], [2020.789, 2021.0384]], 'strong nina': [[2007.8712, 2008.1233], [2010.7041, 2010.9534]], 'weak nino': [[2002.4521, 2003.1233], [2004.6219, 2005.1233], [2006.7041, 2007.0384], [2009.6192, 2010.2], [2015.2, 2016.2877], [2018.7863, 2019.3671], [2023.4521, 2024.0384]], 'moderate nino': [[2002.7041, 2002.9534], [2009.7863, 2010.1233], [2015.4521, 2016.2027], [2023.5342, 2024.0384]], 'strong nino': [[2015.5342, 2016.2027]], 'very strong nino': [[2015.7041, 2016.1233]]} 
PATH_JETSTREAM = '/var/www/html/data/HDF5EOS/gpm_data/'
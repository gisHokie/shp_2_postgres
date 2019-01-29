###################################
#author: Scott D. McDermott
#date: 1/17/2019
#summary: Add compressed shapefiles to postgresql
###################################

# from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# from selenium.common.exceptions import TimeoutException  
# from selenium.common.exceptions import NoSuchElementException

# import requests, zipfile, io, os, sys
# import urllib
import shutil, os
import json
import datetime

#Custom modules
import modules.file_scraper as fs
import modules.shapefile_to_postgres as stp

#import config.config_dbase as db_config
#print(db_config.DATABASE_CONFIG['Postgres']['databases'][0]['host'])

dbasename = 'geo_cat_data'
dserver = 'Postgres'
zip_dir = ''
zip_out_dir =  ''
port = ''
hostname = '' 
username = '' 
pwd = '' 
zip_bkup_dir = ''
shp_names = []
dbase_conn = {}
value_param = []

# Get the current date and time in UTC format
get_datetime = datetime.datetime.utcnow()

# Get the basic info for each data obtained	
json_config = r'E:\platform\scripts\geo_cat\config\config_features.json'
json_config_data = r'E:\platform\scripts\geo_cat\config\config_dbase.json'
feat_json = ''
with open(json_config) as f:
	feat_json = json.load(f)
zip_dir = feat_json["properties"]['in_data']
zip_out_dir = feat_json["properties"]['out_data']
zip_bkup_dir = feat_json["properties"]['backup_data']

# Ensure that the ouput and backup directories exist, if not, build items
if not os.path.exists(zip_out_dir):
    os.makedirs(zip_out_dir)
if not os.path.exists(zip_bkup_dir):
    os.makedirs(zip_bkup_dir)
	
# Get the geo_cat_data database info
with open(json_config_data) as f:
	feat_json = json.load(f)
for j in feat_json:
	if j == dserver:
		for j2 in feat_json[j]['databases']:
			if j2['database_name'] == dbasename:
				len_dbases = len(feat_json[j]['databases'])
				port = j2['port']
				hostname = j2['host']
				username = j2['user']
				pwd = j2['pwd']
	
# Instantiate the scaper class
spr = fs.Scraper()

# Get zip files containing shapes
file_list = []
shp_list = []
# Create a list all files in the directories and sub directories
file_list = spr.get_list_files_from_directory(zip_dir)


#extract the files from the compressed folders
for zip_file in file_list:
	split_z = zip_file.split('\\')
	split_z_file = split_z
	zip_file_path = split_z[2]
	split_zfp = zip_file_path.split('.')
	zip_name = split_zfp[0]
	# add the names to a list for future use
	shp_names.append(zip_name)
	#split the file name to get only name and not name.shp extension
	zip_path = zip_dir + '\\' + zip_name
	print("Extracting : " + zip_name + " into " + zip_out_dir)
	spr.extract_zipname_path(zip_file,zip_out_dir)
	full_shp_dir = zip_out_dir + '\\' + zip_name + '.shp'
	shp_list.append(full_shp_dir)


#UNCOMMENT THIS WHEN READY TO POST TO POSTGRESPost the shapes to Postgres
for shp_path in shp_list:
# shp_path = r'.\out_data\tl_2017_us_state.shp' 
# shp_path = r'.\out_data\tl_2017_us_state_centroid.shp'
	print("Upsizing to Postgres: " + shp_path)
	cmd = 'shp2pgsql -s ' + str(port) + ' ' + shp_path + ' | psql -h ' + hostname +  ' -d ' + dbasename + ' -U ' + username + ' PGPASSWORD ' + pwd + ' -q'
	print(cmd)
	stp.shp_to_postgres(cmd)

# Move the Zip files to a new location
files = os.listdir(zip_dir)
for f in files:
	file_full_path = os.path.join(zip_dir, f)
	shutil.move(file_full_path, zip_bkup_dir)

# Delete the shape files
for the_file in os.listdir(zip_out_dir):
	file_path = os.path.join(zip_out_dir, the_file)
	try:
		if os.path.isfile(file_path):
			os.unlink(file_path)
		#elif os.path.isdir(file_path): shutil.rmtree(file_path)
	except Exception as e:
		print(e)
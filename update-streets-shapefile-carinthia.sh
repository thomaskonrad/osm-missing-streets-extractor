#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/"

. ${DIR}current-time.sh

if [ "$#" -ne 3 ]; then
    echo "Usage: ./update-streets-shapefile-carinthia.sh <log-directory> <shapefile-working-directory> <database-name>"
    exit 1
fi

log_directory=$1
working_directory=$2
database_name=$3

table="carinthia_streets"
link="http://data.ktn.gv.at/fileCount.php?url=http://gis.ktn.gv.at/cache/custom/inspire/INSPIRE_DOWNLOAD/Transport_Network_EPSG31258.zip"
file="Transport_Network_EPSG31258.zip"
shapefile="Transport_Network_EPSG31258.shp"
target_basename="osm-missing-streets-from-ogd-carinthia"

log_file=${log_directory}update-streets-shapefile.log
exec >  >(tee -a ${log_file})
exec 2> >(tee -a ${log_file} >&2)

echo "$(current_time) Starting update of the shapefile containing OGD Carinthia streets that are missing in OSM"

echo "$(current_time) Downloading latest OGD Carinthia street data..."
wget --quiet ${link} -O "${working_directory}${file}"

echo "$(current_time) Unzipping downloaded file..."
unzip -oq "${working_directory}${file}" -d ${working_directory}

echo "$(current_time) Importing OGD Carinthia shapefiles..."
shp2pgsql -W LATIN1 -I -s 31258 "${working_directory}${shapefile}" ${table} | psql -d ${database_name} > /dev/null

echo "$(current_time) Creating tables and converting data..."
psql -d ${database_name} -f ${DIR}create-tables-and-convert-data-carinthia.sql

echo "$(current_time) Calculating street coverage and inserting data into newly created table..."
${DIR}osm-missing-streets-extractor.py -d ${database_name} -r carinthia -t carinthia_streets -P gid -n featurenam -s "Land Kärnten - data.ktn.gv.at; geoimage.at" > /dev/null

echo "$(current_time) Fixing NULL coverage..."
psql -d ${database_name} -f ${DIR}null-coverage-to-zero-coverage.sql

echo "$(current_time) Creating shapefile..."
export PGCLIENTENCODING=LATIN1
pgsql2shp -k -f ${working_directory}${target_basename}.shp ${database_name} \
    "select name, highway, fixme, ST_Transform(geom, 4326), source from carinthia_streets_uncovered where coverage < 50"

# Zip the files and link the zip file to the web root to make it downloadable
shapefile_base_path=${working_directory}${target_basename}
rm ${shapefile_base_path}.zip
zip ${shapefile_base_path}.zip ${shapefile_base_path}.dbf ${shapefile_base_path}.prj ${shapefile_base_path}.shp ${shapefile_base_path}.shx
#ln -s ${working_directory}${target_basename}.zip ${DIR}web/${target_basename}.zip

echo "$(current_time) All done."
#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/"

function current_time()
{
        date +%Y-%m-%d_%H:%M:%S
}

if [ "$#" -ne 3 ]; then
    echo "Usage: ./update-streets-shapefile.sh <log-directory> <shapefile-working-directory> <database-name>"
    exit 1
fi

log_directory=$1
working_directory=$2
database_name=$3

table_low="styria_streets"
table_high="styria_streets_high"
link_low="https://github.com/species/OGD-stmk-daten/raw/master/Stra%C3%9Fennetz/Laendliches%20Strassennetz.zip"
link_high="https://github.com/species/OGD-stmk-daten/raw/master/Stra%C3%9Fennetz/Verkehrsnetz_hochrangig.zip"
file_low="Laendliches Strassennetz.zip"
file_high="Verkehrsnetz_hochrangig.zip"
path_low="Laendliches_Strassennetz.shp"
path_high="Verkehrsnetz_hochrangig.shp"
target_basename="osm-missing-streets-from-ogd-styria"

log_file=${log_directory}update-streets-shapefile.log
exec >  >(tee -a ${log_file})
exec 2> >(tee -a ${log_file} >&2)

echo "$(current_time) Starting update of the shapefile containing OGD Styria streets that are missing in OSM"

echo "$(current_time) Downloading latest OGD Styria street data..."
wget --quiet ${link_low} -O "${working_directory}${file_low}"
wget --quiet ${link_high} -O "${working_directory}${file_high}"

echo "$(current_time) Unzipping downloaded files..."
unzip -oq "${working_directory}${file_low}" -d ${working_directory}
unzip -oq "${working_directory}${file_high}" -d ${working_directory}

echo "$(current_time) Dropping all tables..."
psql -d ${database_name} -f ${DIR}drop-all.sql

echo "$(current_time) Importing OGD Styria shapefiles..."
shp2pgsql -I -s 94258 "${working_directory}${path_low}" ${table_low} | psql -d ${database_name} > /dev/null
shp2pgsql -I -s 94258 "${working_directory}${path_high}" ${table_high} | psql -d ${database_name} > /dev/null

echo "$(current_time) Creating tables and converting data..."
psql -d ${database_name} -f ${DIR}create-tables-and-convert-data.sql

echo "$(current_time) Calculating street coverage and inserting data into newly created table..."
${DIR}osm-missing-streets-extractor.py -d ${database_name} > /dev/null

echo "$(current_time) Fixing NULL coverage..."
psql -d ${database_name} -f ${DIR}null-coverage-to-zero-coverage.sql

echo "$(current_time) Creating shapefile..."
export PGCLIENTENCODING=LATIN1
pgsql2shp -k -f ${working_directory}${target_basename}.shp ${database_name} \
    "select name, highway, fixme, ST_Transform(geom, 4326), source from styria_streets_uncovered where coverage < 50"

# Zip the files and link the zip file to the web root to make it downloadable
shapefile_base_path=${working_directory}${target_basename}
rm ${shapefile_base_path}.zip
zip ${shapefile_base_path}.zip ${shapefile_base_path}.dbf ${shapefile_base_path}.prj ${shapefile_base_path}.shp ${shapefile_base_path}.shx
#ln -s ${working_directory}${target_basename}.zip ${DIR}web/${target_basename}.zip

echo "$(current_time) All done."

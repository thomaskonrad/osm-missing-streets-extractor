#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/"

. ${DIR}current-time.sh

if [ "$#" -ne 3 ]; then
    echo "Usage: ./update-streets-shapefile-carinthia.sh <log-directory> <base-working-directory> <database-name>"
    exit 1
fi

log_directory=$1
base_working_directory=$2
database_name=$3

echo "$(current_time) Dropping all OGD tables..."
psql -d ${database_name} -f ${DIR}drop-all.sql

echo "$(current_time) Pre-calculating OSM street buffers..."
psql -d ${database_name} -f ${DIR}pre-calculate-osm-street-buffers.sql

echo "$(current_time) Creating all shapefiles..."
${DIR}update-streets-shapefile-styria.sh ${log_directory} ${base_working_directory}ogd-styria/ ${database_name}
${DIR}update-streets-shapefile-carinthia.sh ${log_directory} ${base_working_directory}ogd-carinthia/ ${database_name}

echo "$(current_time) All done."

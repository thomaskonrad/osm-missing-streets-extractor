#!/usr/bin/env python3.4

import argparse
import psycopg2
import sys
import progress
import json
import os


def main():
    parser = argparse.ArgumentParser(description="Look for streets in the OGD table that are not covered by "
                                                 "OpenStreetMap and write them into another table.")
    parser.add_argument("-H", "--hostname", dest="hostname", required=False, help="Host name or IP Address")
    parser.add_argument("-d", "--database", dest="database", required=True, help="The name of the database")
    parser.add_argument("-r", "--region", dest="region", required=True, help="The region to extract streets for")
    parser.add_argument("-t", "--table", dest="table", required=True, help="The database table to read from")
    parser.add_argument("-P", "--primary-key", dest="primary_key", required=True, help="The name of the primary key column")
    parser.add_argument("-n", "--name-column", dest="name_column", required=True, help="The name column")
    parser.add_argument("-s", "--source-tag", dest="source_tag", required=True, help="The text that should be written into the OSM source tag")
    parser.add_argument("-u", "--user", dest="user", required=False, help="The database user")
    parser.add_argument("-p", "--password", dest="password", required=False, help="The database password")

    args = parser.parse_args()

    show_progress = False

    # Read and parse the street type mapping file
    street_mapping_select = "null, null,"

    with open(os.path.join(os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__))), "street-type-mapping.json")) as data_file:
        data = json.load(data_file)

        if args.region in data:
            region_data = data[args.region]
            street_mapping_select = "case "

            for highway_mapping_key in region_data["highway"]:
                street_mapping_select += "when s.%s='%s' then '%s'\n" % ("edgecatego", highway_mapping_key, region_data["highway"][highway_mapping_key])

            street_mapping_select += "end as highway, "

            street_mapping_select += "case "

            for fixme_mapping_key in region_data["fixme"]:
                street_mapping_select += "when s.%s='%s' then '%s'\n" % ("edgecatego", fixme_mapping_key, region_data["fixme"][fixme_mapping_key])

            street_mapping_select += "end as fixme, "


    # Try to connect
    try:
        conn = psycopg2.connect(
            host=args.hostname,
            database=args.database,
            user=args.user,
            password=args.password
        )
    except Exception as e:
        print("I am unable to connect to the database (%s)." % e.message)
        sys.exit(1)

    cur = conn.cursor()

    try:
        cur.execute("""
select """ + args.primary_key + """ from """ + args.table + """
where """ + args.primary_key + """ not in (
    select """ + args.primary_key + """ from """ + args.table + """_uncovered
)
        """)
    except Exception as e:
        print("I can't SELECT the not-yet-calculated streets (%s)!" % e)

    rows = cur.fetchall()
    total = len(rows)
    processed = 0

    statement = """
insert into """ + args.table + """_uncovered
    select objectid, name, highway, fixme, geom, source, round(cast((sum(intersection_length) / ogd_length * 100.0) as numeric), 0) as coverage
    from
        (select
            s.""" + args.primary_key + """ as objectid,
            s.""" + args.name_column + """ as name,
            """ + street_mapping_select + """
            ST_AsEWKT(s.geom2) as geom,
            cast('""" + args.source_tag + """' as text) as source,
            ST_Length(ST_Intersection(l.buffer, s.geom2)) as intersection_length,
            ST_Length(s.geom2) as ogd_length
        from osm_street_buffer l
        right join """ + args.table + """ s on (
            ST_Intersects(l.way, ST_Envelope(s.geom2)))
        where s.""" + args.primary_key + """ = %s
        group by """ + args.primary_key + """, """ + args.name_column + """, s.edgecatego, s.geom2, intersection_length) as subquery
    group by objectid, name, highway, fixme, geom, source, ogd_length;
    """

    if show_progress:
        progress.startprogress("Processing all streets")

    for source_street in rows:
        if show_progress:
            percent = processed / total * 100.0
            progress.progress(round(percent, 0))

        objectid = source_street[0]

        try:
            cur.execute(statement, (objectid,))
            conn.commit()
        except Exception as e:
            print("I can't INSERT the data (%s)!" % e)
            sys.exit(1)

        processed += 1

    if show_progress:
        progress.endprogress()


if __name__ == "__main__":
    main()

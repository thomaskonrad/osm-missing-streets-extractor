#!/usr/bin/env python3.4

import argparse
import psycopg2
import sys
from pprint import pprint
import progress


def main():
    parser = argparse.ArgumentParser(description="Calculate the statistical mapping of OGD street types (edgecatego) to"
                                                 "OSM street types (highway).")
    parser.add_argument("-H", "--hostname", dest="hostname", required=True, help="Host name or IP Address")
    parser.add_argument("-d", "--database", dest="database", required=True, help="The name of the database")
    parser.add_argument("-t", "--table", dest="table", required=True, help="The database table to read from")
    parser.add_argument("-P", "--primary-key", dest="primary_key", required=True, help="The name of the primary key column")
    parser.add_argument("-u", "--user", dest="user", required=False, help="The database user")
    parser.add_argument("-p", "--password", dest="password", required=False, help="The database password")

    args = parser.parse_args()

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
        cur.execute("select %s from %s" % (args.primary_key, args.table))
    except Exception as e:
        print("I can't SELECT (%s)!" % e)

    rows = cur.fetchall()
    total = len(rows)
    processed = 0

    street_type_mapping = {}

    progress.startprogress("Processing all streets")

    for source_street in rows:
        percent = processed / total * 100.0
        progress.progress(round(percent, 0))

        objectid = source_street[0]

        statement = """
select
    s.edgecatego as source_type,
    l.highway as target_type,
    sum(ST_Length(ST_Intersection(ST_Buffer(l.way, 10, 'endcap=flat join=round'), s.geom2))) as length
from planet_osm_line l
    left join """ + args.table + """ s on (
            ST_Intersects(l.way, ST_Envelope(s.geom2)) and
            ST_Intersects(s.geom2, ST_Buffer(l.way, 10, 'endcap=flat join=round'))
        )
    where
        l.highway is not null
        and s.""" + args.primary_key + """ = %s
    group by edgecatego, highway
        """

        try:
            cur.execute(statement, (objectid,))
            results = cur.fetchall()

            for result in results:

                source_type = result[0]
                target_type = result[1]
                length = result[2]

                if not source_type in street_type_mapping:
                    street_type_mapping[source_type] = {}

                if target_type in street_type_mapping[source_type]:
                    street_type_mapping[source_type][target_type] += length
                else:
                    street_type_mapping[source_type][target_type] = length
        except Exception as e:
            print("I can't SELECT (%s)!" % e)
            sys.exit(1)

        processed += 1

    pprint(street_type_mapping)


if __name__ == "__main__":
    main()

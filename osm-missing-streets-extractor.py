#!/usr/bin/env python3.4

import argparse
import psycopg2
import sys
import progress


def main():
    parser = argparse.ArgumentParser(description="Look for streets in the OGD table that are not covered by "
                                                 "OpenStreetMap and write them into another table.")
    parser.add_argument("-H", "--hostname", dest="hostname", required=False, help="Host name or IP Address")
    parser.add_argument("-d", "--database", dest="database", required=True, help="The name of the database")
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
        cur.execute("""
select objectid from styria_streets
where objectid not in (
    select objectid from styria_streets_uncovered
)
        """)
    except Exception as e:
        print("I can't SELECT the not-yet-calculated streets (%s)!" % e)

    rows = cur.fetchall()
    total = len(rows)
    processed = 0

    progress.startprogress("Processing all streets")

    for source_street in rows:
        percent = processed / total * 100.0
        progress.progress(round(percent, 0))

        objectid = source_street[0]

        statement = """
insert into styria_streets_uncovered
    select
        s.objectid as objectid,
        s.nametext as name,
        case -- "highway" tag (pretty deterministic mapping)
            when s.edgecatego='A' then 'motorway'       -- Autobahn
            when s.edgecatego='S' then 'motorway'       -- Schnellstraße
            when s.edgecatego='B' then 'primary'        -- Bundesstraße
            when s.edgecatego='L' then 'secondary'      -- Landesstraße
        end,
        case -- "fixme" tag (too undeterministic mapping)
            when s.edgecatego='P'  then 'highway=secondary (46 %%), unclassified (20 %%), service (19 %%). Please delete this tag after the classification.'                  -- Öffentliche Privatstraße (z.B. Großglockner Hochalpenstraße)
            when s.edgecatego='G'  then 'highway=unclassified (44 %%), residential (28 %%), service (10 %%). Please delete this tag after the classification.'                -- Gemeindestraße
            when s.edgecatego='I'  then 'highway=unclassified (36 %%), track (24 %%), service (21 %%), residential (15 %%). Please delete this tag after the classification.' -- Interessentenstraße
            when s.edgecatego='PS' then 'highway=service (36 %%), track (26 %%), unclassified (21 %%), residential (14 %%). Please delete this tag after the classification.' -- Privatstraße
        end,
        ST_AsEWKT(s.geom2) as geom,
        'Land Steiermark - data.steiermark.gv.at; geoimage.at' as source,
        round(cast((sum(ST_Length(ST_Intersection(l.buffer, s.geom2))) / ST_Length(s.geom2) * 100.0) as numeric), 0) as coverage
    from osm_street_buffer l
    right join styria_streets s on (
        ST_Intersects(l.way, ST_Envelope(s.geom2)))
    where s.objectid = %s
    group by objectid, nametext, s.edgecatego, s.geom2;
        """

        try:
            cur.execute(statement, (objectid,))
            conn.commit()
        except Exception as e:
            print("I can't INSERT the data (%s)!" % e)
            sys.exit(1)

        processed += 1

    progress.endprogress()


if __name__ == "__main__":
    main()

-- Add a second geom column so that we can convert the original one to the 900913 SRS
alter table styria_streets add column geom2 geometry(LineString,900913);

-- Convert the geom
update styria_streets set geom2 = ST_Transform(ST_LineMerge(geom), 900913);

-- Linestrings from styria high
insert into styria_streets
    select
    gid + 1000000, objectid + 1000000, strcat, namealias, shape_leng,
    null,
    ST_Transform(ST_LineMerge(ST_Force_2D(geom)), 900913)
    from styria_streets_high
    where GeometryType(ST_LineMerge(geom))='LINESTRING';

-- Split up multilinestrings from styria high
create sequence seq_styria_streets_high minvalue 2100000;

insert into styria_streets
    select
    nextval('seq_styria_streets_high'), currval('seq_styria_streets_high'),
    strcat, namealias, shape_leng,
    null,
    ST_Transform((ST_Dump(ST_Force_2D(geom))).geom, 900913)
    from styria_streets_high
    where GeometryType(ST_LineMerge(geom))='MULTILINESTRING';

drop sequence seq_styria_streets_high;

-- Drop the "styria_streets_high" table as we don't need it any more
drop table if exists styria_streets_high;

-- Create the "styria_streets_uncovered" table
CREATE TABLE styria_streets_uncovered
(
    objectid integer,
    name character varying(254),
    highway character varying(254),
    geom geometry(LineString,900913),
    source character varying(254),
    coverage integer,
    CONSTRAINT styria_streets_uncovered_pkey PRIMARY KEY (objectid)
);

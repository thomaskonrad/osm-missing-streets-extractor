-- Add a second geom column so that we can convert the original one to the 900913 SRS
alter table carinthia_streets add column geom2 geometry(LineString,900913);

-- Convert the geom
update carinthia_streets set geom2 = ST_Transform(ST_LineMerge(geom), 900913);

-- Create the "carinthia_streets_uncovered" table
CREATE TABLE carinthia_streets_uncovered
(
    objectid integer,
    name character varying(254),
    highway character varying(254),
    fixme character varying(254),
    geom geometry(LineString,900913),
    source character varying(254),
    coverage integer,
    CONSTRAINT carinthia_streets_uncovered_pkey PRIMARY KEY (objectid)
);

-- Create an index on the objectid column
create index idx_carinthia_streets_gid ON carinthia_streets (gid);

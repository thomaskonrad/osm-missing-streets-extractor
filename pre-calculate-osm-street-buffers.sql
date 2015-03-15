-- Pre-calculate way buffers to speed everything up
drop table if exists osm_street_buffer;

create table osm_street_buffer
(
    way geometry(LineString,900913),
    buffer geometry(Geometry,900913)
);

create index osm_street_buffer_way on osm_street_buffer using gist (way);
create index osm_street_buffer_buffer on osm_street_buffer using gist (buffer);

insert into osm_street_buffer
    select way, ST_Buffer(way, 10, 'endcap=flat join=round')
    from planet_osm_line
    where highway is not null
    and ST_Intersects(
        GeomFromEWKT(
            'SRID=900913;POLYGON((1509864.99 5878969.16,1509864.99 6078269.47,1800230.82 6078269.47,1800230.82 5878969.16,1509864.99 5878969.16))'
        ),
        way
    )
    or ST_Intersects(
        GeomFromEWKT(
            'SRID=900913;POLYGON((1408952.55 5840208.75,1408952.55 5963531.56,1677044.9 5963531.56,1677044.9 5840208.75,1408952.55 5840208.75))'
        ),
        way
    );

-- If the OGD way is not at all touched by an OSM way, the coverage is NULL instead of 0. This is because ST_Length
-- of NULL does not return 0, but null. Fixing this with the following query.
update styria_streets_uncovered set coverage = 0 where coverage is null;

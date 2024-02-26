CREATE TABLE stations (
    address VARCHAR(100),
	code_district VARCHAR(100),
	code_suburb VARCHAR(100),
	dock_bikes VARCHAR(100),
	free_bases VARCHAR(100),
	id INT,
	light VARCHAR(100), 
	name VARCHAR(100),
	no_available VARCHAR(100),
	number VARCHAR(100),
	reservations_count VARCHAR(100),
	total_bases VARCHAR(100),
	date_time TIMESTAMP,
	longitude VARCHAR(100),
	latitude VARCHAR(100),
	coordinates VARCHAR(100)
);

SELECT * FROM stations;

ALTER TABLE stations RENAME COLUMN date_time TO last_updated;

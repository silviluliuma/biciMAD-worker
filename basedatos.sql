CREATE TABLE estaciones(
	address VARCHAR(100),
	code_district VARCHAR(100),
	code_suburb VARCHAR(100),
	id INT,
	name VARCHAR(100),
	number VARCHAR(100),
	total_bases VARCHAR(100),
	last_updated TIMESTAMP,
	longitude VARCHAR(100),
	latitude VARCHAR(100),
	coordinates VARCHAR(100)
);

INSERT INTO estaciones (address, code_district, code_suburb, id, name, total_bases, longitude, latitude, coordinates, last_updated)
SELECT address, code_district, code_suburb, id, name, total_bases, longitude, latitude, coordinates, last_updated
FROM stations;

CREATE TABLE disponibilidad(
	dock_bikes VARCHAR(100),
	free_bases VARCHAR(100),
	id INT,
	light VARCHAR(100), 
	no_available VARCHAR(100),
	reservations_count VARCHAR(100),
	last_updated TIMESTAMP
);

INSERT INTO disponibilidad (dock_bikes, free_bases, light, no_available, reservations_count, id, last_updated)
SELECT dock_bikes, free_bases, light, no_available, reservations_count, id, last_updated
FROM stations;

SELECT * FROM estaciones;
SELECT * FROM disponibilidad
ORDER BY last_updated DESC;

DELETE FROM estaciones
WHERE last_updated <> '2024-02-19 18:28:00';

ALTER TABLE disponibilidad
ADD COLUMN activate INT;
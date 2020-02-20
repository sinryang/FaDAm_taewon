CREATE TABLE sensors(
		id SERIAL PRIMARY KEY,
		ip text NOT NULL,
		port int NOT NULL,
		sensor_name text NOT NULL,
		description text,
		status text DEFAULT 'stopped'

);

CREATE TABLE lvdt_data(
		data_id BIGSERIAL,
		date timestamp with time zone NOT NULL,
		date_cnt SERIAL NOT NULL,
		axial real NOT NULL,
		radial real NOT Null,
		data_stat text NOT Null,
		sensor_id int NOT NULL,
		id_char text DEFAULT 'AA'
);

CREATE TABLE curr_id(
		name text PRIMARY KEY,
		id_char text DEFAULT 'AA'
);

INSERT INTO curr_id (name) VALUES
	('id_char');

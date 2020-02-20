INSERT INTO lvdt_data (date,date_cnt,axial,radial,data_stat,sensor_id) VALUES
	(current_timestamp, 1, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 2, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 3, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 4, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 5, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 6, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 7, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 8, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 9, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 10, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 11, 231.12, 13.12, 'OK', 1),
	(current_timestamp, 12, 231.12, 13.12, 'OK', 1);

INSERT INTO sensors (id,ip,port,sensor_name,description) VALUES
	(1, '127.0.0.1', '4321', 'sensor_1',''),
	(2, '127.0.0.1', '4321', 'sensor_2',''),
	(3, '127.0.0.1', '4321', 'sensor_3','');

DROP DATABASE IF EXISTS SalesDB;

CREATE DATABASE IF NOT EXISTS SalesDB;

USE SalesDB;

DROP TABLE IF EXISTS models;    
DROP TABLE IF EXISTS datasets;

CREATE TABLE datasets (
    dataset_id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    dataset_name VARCHAR(255) NOT NULL,
    bucketkey VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE models (
    model_id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    dataset_id INT NOT NULL,
    bucketkey_model VARCHAR(512) NOT NULL,
    created_at_model TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_type VARCHAR(255),
    hyperparameters JSON,
    FOREIGN KEY (dataset_id) REFERENCES datasets(dataset_id)
);

ALTER TABLE datasets AUTO_INCREMENT = 1001;
ALTER TABLE models AUTO_INCREMENT = 80001;

CREATE USER 'salesdb-read-only' IDENTIFIED BY 'abc123!!';
CREATE USER 'salesdb-read-write' IDENTIFIED BY 'def456!!';


GRANT SELECT, SHOW VIEW ON SalesDB.* 
      TO 'salesdb-read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON SalesDB.* 
      TO 'salesdb-read-write';
      
FLUSH PRIVILEGES;

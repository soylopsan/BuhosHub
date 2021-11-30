# BuhosHub

mysql -u root -p

CREATE DATABASE buhoshub;

USE buhoshub;

CREATE TABLE usuarios(id SERIAL PRIMARY KEY, nombre VARCHAR(100), correoelectronico VARCHAR(100), nombreusuario VARCHAR(30), contrasena VARCHAR(100), fecharegistro TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE entradas (id INT (11) AUTO_INCREMENT PRIMARY KEY, materia VARCHAR(255), editor VARCHAR (100), descripcion TEXT, fechacreacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ;

use Closet;

DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS garment;
DROP TABLE IF EXISTS reservation;
DROP TABLE IF EXISTS tag;

SET FOREIGN_KEY_CHECKS=0;

CREATE TABLE person (
	person_id int not null auto_increment,
	name varchar(10) not null,
	password varchar(20),
	primary key(person_id)
) ENGINE=InnoDB;

CREATE TABLE garment (
	garment_id int not null auto_increment,
	description varchar(50),
	photo_loc varchar(100),
	person_id int not null,
	tag_garmenttype_id int not null,
	tag_color_id int not null,
	tag_size_id int not null,
	foreign key (person_id) REFERENCES person(person_id) ON UPDATE CASCADE ON DELETE RESTRICT,
	foreign key (tag_garmenttype_id) REFERENCES tag(tag_id) ON UPDATE CASCADE,
	foreign key (tag_color_id) REFERENCES tag(tag_id) ON UPDATE CASCADE,
	foreign key (tag_size_id) REFERENCES tag(tag_id) ON UPDATE CASCADE,
	primary key (garment_id)
) ENGINE=InnoDB;

CREATE TABLE reservation (
	reservation_id int not null auto_increment,
	date_start date not null,
	date_end date not null,
	person_id int not null,
	garment_id int not null,
	foreign key (person_id) REFERENCES person(person_id) ON UPDATE CASCADE ON DELETE RESTRICT,
	foreign key (garment_id) REFERENCES garment(garment_id) ON UPDATE CASCADE ON DELETE RESTRICT,
	primary key (reservation_id)
) ENGINE=InnoDB;

CREATE TABLE tag (
	tag_id int not null auto_increment,
	tag_name varchar(50),
	feature_type ENUM('garment type', 'color', 'size'),
	primary key (tag_id)
) ENGINE=InnoDB;

INSERT INTO person (name, password) VALUES ('user1', 'foo123');

INSERT INTO tag
(tag_name, feature_type)
VALUES
('accessory','garment type'),
('bottoms','garment type'),
('dress','garment type'),
('other','garment type'),
('outerwear','garment type'),
('shoes','garment type'),
('top','garment type'),
('beige','color'),
('black','color'),
('blue','color'),
('brown','color'),
('gold','color'),
('green','color'),
('grey','color'),
('multicolor','color'),
('pink','color'),
('purple','color'),
('red','color'),
('white','color'),
('other','color'),
('xxs','size'),
('xs','size'),
('s','size'),
('m','size'),
('l','size'),
('xl','size'),
('xxl','size'),
('onesize','size'),
('other','size');

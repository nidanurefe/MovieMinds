CREATE DATABASE movie_review_db;
USE movie_review_db;

CREATE TABLE genres (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE producers (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE movies (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    release_year INT NOT NULL,
    rating DECIMAL(3,1) NOT NULL,
    genre_id INT NOT NULL,
    cover_image VARCHAR(255),
    producer_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (genre_id) REFERENCES genres(id),
    FOREIGN KEY (producer_id) REFERENCES producers(id)
);

CREATE TABLE actors (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    img_url VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE movie_actors (
    movie_id INT NOT NULL,
    actor_id INT NOT NULL,
    PRIMARY KEY (movie_id, actor_id),
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES actors(id) ON DELETE CASCADE
);

CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE user_favorite_movies (
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    PRIMARY KEY (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
);

CREATE TABLE user_favorite_actors (
    user_id INT NOT NULL,
    actor_id INT NOT NULL,
    PRIMARY KEY (user_id, actor_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES actors(id) ON DELETE CASCADE
);

CREATE TABLE reviews (
    id INT NOT NULL AUTO_INCREMENT,
    movie_id INT NOT NULL,
    user_id INT NOT NULL,
    review_text TEXT NOT NULL,
    rating DECIMAL(3,1) NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

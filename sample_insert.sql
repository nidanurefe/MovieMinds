-- Insert genres
INSERT INTO genres (name) VALUES 
('Action'), 
('Comedy'), 
('Drama'), 
('Romance'), 
('Sci-Fi'), 
('Horror');

-- Insert producers
INSERT INTO producers (name) VALUES 
('Warner Bros'), 
('Universal Pictures'), 
('Paramount Pictures'), 
('Marvel Studios'), 
('Sony Pictures'),
('20th Century Fox'),
('Columbia Pictures'),
('Lionsgate'),
('New Line Cinema'),
('Pixar Animation Studios');

-- Insert movies
INSERT INTO movies (title, release_year, rating, genre_id, cover_image, producer_id) VALUES 
('Avengers: Endgame', 2019, 8.4, 1, 'https://tr.web.img4.acsta.net/pictures/19/03/28/11/29/4805705.jpg', 4),
('The Dark Knight', 2008, 9.0, 1, 'https://m.media-amazon.com/images/S/pv-target-images/8753733ac616155963cc440c3cf5367f45d7685b672c5b9c35bc7f182aec17c4.jpg', 1),
('Forrest Gump', 1994, 8.8, 3, 'https://upload.wikimedia.org/wikipedia/tr/b/bb/Forrest_Gump_%28film%2C_1994%29.jpg', 2),
('The Notebook', 2004, 7.8, 4, 'https://tr.web.img4.acsta.net/pictures/bzp/03/47422.jpg', 5),
('Inception', 2010, 8.8, 5, 'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_FMjpg_UX1000_.jpg', 3),
('The Conjuring', 2013, 7.5, 6, 'https://tr.web.img4.acsta.net/c_310_420/img/b8/d8/b8d861a733625a283e7b3dbc1864489c.jpg', 1),
('Titanic', 1997, 7.8, 4, 'https://m.media-amazon.com/images/M/MV5BYzYyN2FiZmUtYWYzMy00MzViLWJkZTMtOGY1ZjgzNWMwN2YxXkEyXkFqcGc@._V1_.jpg', 2), 
('The Matrix', 1999, 8.7, 5, 'https://upload.wikimedia.org/wikipedia/tr/3/36/Matrix-film.jpg', 1),
('Deadpool', 2016, 8.0, 1, 'https://m.media-amazon.com/images/I/51Gh9OaWVcL._AC_UF1000,1000_QL80_.jpg', 3),
('Hunger Games', 2012, 7.2, 1, 'https://m.media-amazon.com/images/M/MV5BMTcxNDI2NDAzNl5BMl5BanBnXkFtZTgwODM3MTc2MjE@._V1_.jpg', 4),
('Up', 2009, 8.2, 5, 'https://upload.wikimedia.org/wikipedia/en/0/05/Up_%282009_film%29.jpg', 5);

-- Insert actors
INSERT INTO actors (name, img_url) VALUES 
('Robert Downey Jr.', 'https://media.themoviedb.org/t/p/w500/5qHNjhtjMD4YWH3UP0rm4tKwxCL.jpg'),
('Christian Bale', 'https://m.media-amazon.com/images/M/MV5BMTkxMzk4MjQ4MF5BMl5BanBnXkFtZTcwMzExODQxOA@@._V1_.jpg'),
('Tom Hanks', 'https://m.media-amazon.com/images/M/MV5BMTQ2MjMwNDA3Nl5BMl5BanBnXkFtZTcwMTA2NDY3NQ@@._V1_FMjpg_UX1000_.jpg'),
('Ryan Gosling', 'https://tr.web.img3.acsta.net/c_310_420/pictures/16/05/17/17/28/208580.jpg'),
('Leonardo DiCaprio', 'https://tr.web.img4.acsta.net/c_310_420/medias/nmedia/18/35/52/66/20426137.jpg'),
('Vera Farmiga', 'https://images.mubicdn.net/images/cast_member/23765/cache-650230-1628157376/image-w856.jpg'),
('Kate Winslet', 'https://tr.web.img3.acsta.net/c_310_420/pictures/15/09/15/10/01/065591.jpg'),
('Keanu Reeves', 'https://m.media-amazon.com/images/M/MV5BNDEzOTdhNDUtY2EyMy00YTNmLWE5MjItZmRjMmQzYTRlMGRkXkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg'),
('Ryan Reynolds', 'https://upload.wikimedia.org/wikipedia/commons/1/14/Deadpool_2_Japan_Premiere_Red_Carpet_Ryan_Reynolds_%28cropped%29.jpg'),
('Jennifer Lawrence', 'https://tr.web.img4.acsta.net/c_310_420/pictures/15/12/24/11/47/487503.jpg');

-- Insert movie_actors relationships
INSERT INTO movie_actors (movie_id, actor_id) VALUES 
(1, 1),  -- Avengers: Endgame - Robert Downey Jr.
(2, 2),  -- The Dark Knight - Christian Bale
(3, 3),  -- Forrest Gump - Tom Hanks
(4, 4),  -- The Notebook - Ryan Gosling
(5, 5),  -- Inception - Leonardo DiCaprio
(6, 6),  -- The Conjuring - Vera Farmiga
(7, 7),  -- Titanic - Kate Winslet
(8, 8),  -- The Matrix - Keanu Reeves
(9, 9),  -- Deadpool - Ryan Reynolds
(10, 10), -- Hunger Games - Jennifer Lawrence
(11, 3);  -- Up - Tom Hanks

-- Insert users
INSERT INTO users (username, password, email, first_name, last_name) VALUES 
('john_doe', 'password123', 'john.doe@email.com', 'John', 'Doe'),
('jane_smith', 'password456', 'jane.smith@email.com', 'Jane', 'Smith');

-- Insert user_favorite_movies relationships
INSERT INTO user_favorite_movies (user_id, movie_id) VALUES 
(1, 1),  -- John Doe's favorite movie: Avengers: Endgame
(1, 3),  -- John Doe's favorite movie: Forrest Gump
(2, 2),  -- Jane Smith's favorite movie: The Dark Knight
(1, 7),  -- John Doe's favorite movie: Titanic
(2, 8),  -- Jane Smith's favorite movie: The Matrix
(1, 9);  -- John Doe's favorite movie: Deadpool

-- Insert user_favorite_actors relationships
INSERT INTO user_favorite_actors (user_id, actor_id) VALUES 
(1, 1),  -- John Doe's favorite actor: Robert Downey Jr.
(2, 2),  -- Jane Smith's favorite actor: Christian Bale
(1, 3),  -- John Doe's favorite actor: Kate Winslet
(2, 4),  -- Jane Smith's favorite actor: Keanu Reeves
(1, 5);  -- John Doe's favorite actor: Ryan Reynolds

-- Insert reviews
INSERT INTO reviews (movie_id, user_id, review_text, rating) VALUES 
(1, 1, 'Amazing movie, a perfect conclusion to the saga.', 9.5),  -- Avengers: Endgame - John Doe
(2, 2, 'A fantastic performance by Christian Bale, one of the best Batman films.', 9.0),  -- The Dark Knight - Jane Smith
(3, 1, 'A heartwarming story that will make you cry.', 8.5),  -- Forrest Gump - John Doe
(7, 1, 'A timeless classic, great chemistry between the leads.', 9.0),  -- Titanic - John Doe
(8, 2, 'One of the most innovative sci-fi films, a must-see.', 9.5),  -- The Matrix - Jane Smith
(9, 1, 'Hilarious and action-packed, Ryan Reynolds nails the role.', 8.5);  -- Deadpool - John Doe
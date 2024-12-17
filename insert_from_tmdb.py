import requests, pymysql.connections, os
from app import createApp  
from dotenv import load_dotenv

app = createApp()
load_dotenv()

API_KEY = os.getenv('API_KEY') # Get the API key from the environment variables
BASE_URL = 'https://api.themoviedb.org/3' # Base URL for the TMDB API
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500" # Base URL for the images

# ***** Function to connect to the database *****
def get_db_connection(app)->pymysql.Connection:
    return pymysql.connect( # Connect to the database
        host=app.config['MYSQL_HOST'], 
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


# ***** Functions to fetch data from API *****

# Function to fetch movies from the TMDB API
def get_movies(page=1)->dict:
    url:str = f"{BASE_URL}/discover/movie" # Endpoint to fetch movies
    headers:list = { # Headers to be sent with the request
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    params:list = { # Parameters to be sent with the request
        "include_adult": "false",
        "language": "en-US",
        "page": page,
        "sort_by": "popularity.desc"
    }
    response:dict = requests.get(url, headers=headers, params=params) # Send the request
    if response.status_code == 200: # Check if the request was successful
        return response.json() # Return the response as a JSON object
    else: # If the request was not successful
        print(f"Failed to fetch data: {response.status_code}") # Print an error message
        return None # Return None if the request was not successful


# Function to fetch the cast of a movie from the TMDB API
def get_movie_cast(movie_id)->list:
    url:str= f"{BASE_URL}/movie/{movie_id}/credits" # Endpoint to fetch the cast of a movie
    headers = { # Headers to be sent with the request
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers) # Send the request
    if response.status_code == 200: # Check if the request was successful
        return response.json().get('cast', []) # Return the cast of the movie
    else: # If the request was not successful
        print(f"Failed to fetch cast for movie {movie_id}: {response.status_code}")   # Print an error message
        return [] # Return an empty list if the request was not successful


# Function to fetch the genres from the TMDB API
def get_genres()->list:  
    url:str = f"{BASE_URL}/genre/movie/list" # Endpoint to fetch the genres
    headers:list = { # Headers to be sent with the request
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    response:dict = requests.get(url, headers=headers) # Send the request
    if response.status_code == 200: # Check if the request was successful
        return response.json().get('genres', []) # Return the genres
    else: # If the request was not successful
        print(f"Failed to fetch genres: {response.status_code}") # Print an error message
        return [] # Return an empty list if the request was not successful
    

# Function to fetch the details of a movie from the TMDB API
def get_movie_details(movie_id)->dict: 
    url:str = f"{BASE_URL}/movie/{movie_id}" # Endpoint to fetch the details of a movie
    headers:list = { # Headers to be sent with the request
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    response:dict = requests.get(url, headers=headers) # Send the request
    if response.status_code == 200: # Check if the request was successful
        return response.json() # Return the details of the movie
    else: # If the request was not successful
        print(f"Failed to fetch movie details for {movie_id}: {response.status_code}") # Print an error message
        return None # Return None if the request was not successful

# ***** Functions to insert data into database *****

# Function to insert a movie into the database
def insert_movie(connection, movie) -> None:
    with connection.cursor() as cursor:   # Create a cursor object
        genre_id:int = movie['genre_ids'][0] if movie['genre_ids'] else None # Get the genre ID
        movie_details:dict = get_movie_details(movie['id']) # Fetch the details of the movie
        if movie_details: # If the details are fetched successfully
            producers = movie_details.get('production_companies', []) # Get the producers of the movie
            if producers: # If producers are found
                producer_id = producers[0]['id'] # Get the ID of the first producer
                producer_name = producers[0]['name'] # Get the name of the first producer
                insert_producer(connection, producer_id, producer_name) # Insert the producer into the database
        print(movie_details['production_companies'][0]) # Print the producer of the movie for debugging purposes
        poster_path:str = IMAGE_BASE_URL + movie.get('poster_path', '') # Get the poster path of the movie

        check_sql = "SELECT COUNT(*) AS count FROM movies WHERE tmdb_id = %s" # SQL query to check if the movie already exists
        cursor.execute(check_sql, (movie['id'],)) # Execute the query
        result:dict = cursor.fetchone() # Fetch the result of the query
 
        count:int = result['count'] if isinstance(result, dict) else result[0] # Get the count of the result

        if count == 0:   # If the movie does not exist in the database
            sql = """  # SQL query to insert the movie into the database
            INSERT INTO movies (tmdb_id, title, release_year, rating, genre_id, cover_image, producer_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, ( # Execute the query
                movie['id'],
                movie['title'],
                movie['release_date'][:4] if 'release_date' in movie and movie['release_date'] else None,
                movie.get('vote_average', 0),
                genre_id,
                poster_path,
                movie_details['production_companies'][0]['id']
            ))
            connection.commit() # Commit the transaction 
        else: # If the movie already exists in the database
            print(f"Movie with tmdb_id {movie['id']} already exists.")  # Print a message
            connection.commit() # Commit the transaction
            return # Return from the function

# Function to insert a producer into the database
def insert_producer(connection, producer_id, producer_name)->None: 
    with connection.cursor() as cursor: # Create a cursor object
        cursor.execute("SELECT id FROM producers WHERE id = %s", (producer_id,)) # Execute a query to check if the producer already exists
        result:dict = cursor.fetchone() # Fetch the result of the query
        
        if not result:   # If the producer does not exist in the database
            sql = """ 
            INSERT INTO producers (id, name)
            VALUES (%s, %s)
            """
            cursor.execute(sql, (producer_id, producer_name)) # Execute the query
        connection.commit() # Commit the transaction


# Function to insert an actor into the database
def insert_actor(connection, actor_id, actor_name, img_url=None) -> None:
    img_url:str= IMAGE_BASE_URL + img_url if img_url else None # Get the image URL of the actor 

    with connection.cursor() as cursor: # Create a cursor object
        check_sql = "SELECT COUNT(*) AS count FROM actors WHERE id = %s" # SQL query to check if the actor already exists
        cursor.execute(check_sql, (actor_id,)) # Execute the query
        result:dict = cursor.fetchone() # Fetch the result of the query

        count:int = result['count'] if isinstance(result, dict) else result[0] # Get the count of the result

        if count == 0: # If the actor does not exist in the database
            sql = """ 
            INSERT INTO actors (id, name, img_url)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (actor_id, actor_name, img_url)) # Execute the query
            connection.commit() # Commit the transaction
        else: # If the actor already exists in the database
            print(f"Actor with id {actor_id} already exists.") # Print a message
            connection.commit() # Commit the transaction
            return # Return from the function

# Function to insert a genre into the database
def insert_genre(connection, genre_id, genre_name="Unknown")->None: 
    with connection.cursor() as cursor: # Create a cursor object
        sql = """
        INSERT IGNORE INTO genres (id, name)
        VALUES (%s, %s)
        """
        cursor.execute(sql, (genre_id, genre_name)) # Execute the query
    connection.commit() # Commit the transaction


# Function to insert a movie-actor pairing into the database
def insert_movie_actor(connection, movie_id, actor_id) -> None:
    try: 
        with connection.cursor() as cursor: # Create a cursor object
            check_sql = """ 
            SELECT COUNT(*) AS count 
            FROM movie_actors 
            WHERE movie_id = %s AND actor_id = %s
            """
            cursor.execute(check_sql, (movie_id, actor_id)) # Execute the query
            result:dict = cursor.fetchone() # Fetch the result of the query

            count:int = result['count'] if isinstance(result, dict) else result[0] # Get the count of the result

            if count == 0: # If the pairing does not exist in the database
                sql = """
                INSERT INTO movie_actors (movie_id, actor_id)
                VALUES (%s, %s)
                """
                cursor.execute(sql, (movie_id, actor_id)) # Execute the query
                connection.commit() # Commit the transaction
                print(f"Inserted movie_id {movie_id} and actor_id {actor_id} into movie_actors.") # Print a message
            else: # If the pairing already exists in the database
                print(f"The pairing movie_id {movie_id} and actor_id {actor_id} already exists.") # Print a message
    except Exception as e: # If an error occurs
        print(f"An error occurred: {e}") # Print the error message


# Function to link a movie with its producers
def link_movie_producers(connection, movie_id)->None: 
    movie_details:dict = get_movie_details(movie_id) # Fetch the details of the movie
    if not movie_details: # If the details are not fetched successfully
        return # Return from the function
    producers:dict = movie_details.get('production_companies', []) # Get the producers of the movie
    for producer in producers: # Iterate over the producers
        producer_id:int = producer['id'] # Get the ID of the producer
        producer_name:int = producer['name'] # Get the name of the producer
        insert_producer(connection, producer_id, producer_name) # Insert the producer into the database

# Function to insert all genres into the database
def insert_all_genres(connection)->None: 
    genres:dict = get_genres() # Fetch the genres
    for genre in genres: # Iterate over the genres
        insert_genre(connection, genre['id'], genre['name']) # Insert the genre into the database

def main():
    connection:pymysql.Connection = get_db_connection(app) # Get a database connection
    insert_all_genres(connection)   # Insert all genres into the database
    movies_data:dict = get_movies(page=1) # Fetch the movies
      
    if movies_data: # If the movies are fetched successfully
        for movie in movies_data['results']: # Iterate over the movies
            try: 
                link_movie_producers(connection, movie['id']) # Link the movie with its producers
            except Exception as e:
                print(f"Error adding producers for movie {movie['id']}: {e}") # Print an error message

            for movie in movies_data['results']:  # Iterate over the movies
                insert_movie(connection, movie) # Insert the movie into the database
            
            for movie in movies_data['results']: # Iterate over the movies

                cast:dict = get_movie_cast(movie['id']) # Fetch the cast of the movie
                for actor in cast: # Iterate over the cast
                    actor_id:int = actor.get('id') # Get the ID of the actor
                    actor_name:int = actor.get('name') # Get the name of the actor
                    img_url:str = actor.get('profile_path', None) # Get the image URL of the actor

                    if actor_id and actor_name: # If the actor ID and name are found
                        insert_actor(connection, actor_id, actor_name, img_url) # Insert the actor into the database
                        insert_movie_actor(connection, movie['id'], actor_id) # Insert the movie-actor pairing into the database
    
    connection.close() # Close the database connection


if __name__ == "__main__": 
    main()
import requests
import pymysql
import os
from app import createApp  
from dotenv import load_dotenv

app = createApp()
load_dotenv()

API_KEY = os.getenv('API_KEY')
BASE_URL = 'https://api.themoviedb.org/3'
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

def get_db_connection(app):
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def get_movies(page=1)->dict:
    url = f"{BASE_URL}/discover/movie"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    params = {
        "include_adult": "false",
        "language": "en-US",
        "page": page,
        "sort_by": "popularity.desc"
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

def get_movie_cast(movie_id)->list:
    url = f"{BASE_URL}/movie/{movie_id}/credits"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('cast', [])
    else:
        print(f"Failed to fetch cast for movie {movie_id}: {response.status_code}")
        return []

def get_genres()->list:
    url = f"{BASE_URL}/genre/movie/list"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('genres', [])
    else:
        print(f"Failed to fetch genres: {response.status_code}")
        return []
    


def get_movie_details(movie_id)->dict:
    url = f"{BASE_URL}/movie/{movie_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch movie details for {movie_id}: {response.status_code}")
        return None

def insert_movie(connection, movie) -> None:
    with connection.cursor() as cursor:  
        genre_id = movie['genre_ids'][0] if movie['genre_ids'] else None
        movie_details = get_movie_details(movie['id'])
        if movie_details:
            producers = movie_details.get('production_companies', [])
            if producers:
                producer_id = producers[0]['id']
                producer_name = producers[0]['name']
                insert_producer(connection, producer_id, producer_name)
        print(movie_details['production_companies'][0])
        poster_path = IMAGE_BASE_URL + movie.get('poster_path', '')

        check_sql = "SELECT COUNT(*) AS count FROM movies WHERE tmdb_id = %s"
        cursor.execute(check_sql, (movie['id'],))
        result = cursor.fetchone()

        count = result['count'] if isinstance(result, dict) else result[0]

        if count == 0:  
            sql = """
            INSERT INTO movies (tmdb_id, title, release_year, rating, genre_id, cover_image, producer_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                movie['id'],
                movie['title'],
                movie['release_date'][:4] if 'release_date' in movie and movie['release_date'] else None,
                movie.get('vote_average', 0),
                genre_id,
                poster_path,
                movie_details['production_companies'][0]['id']
            ))
            connection.commit()
        else:
            print(f"Movie with tmdb_id {movie['id']} already exists.")
            connection.commit()
            return


def insert_producer(connection, producer_id, producer_name)->None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT id FROM producers WHERE id = %s", (producer_id,))
        result = cursor.fetchone()
        
        if not result:  
            sql = """
            INSERT INTO producers (id, name)
            VALUES (%s, %s)
            """
            cursor.execute(sql, (producer_id, producer_name))
        connection.commit()




def insert_actor(connection, actor_id, actor_name, img_url=None) -> None:
    img_url = IMAGE_BASE_URL + img_url if img_url else None

    with connection.cursor() as cursor:
        check_sql = "SELECT COUNT(*) AS count FROM actors WHERE id = %s"
        cursor.execute(check_sql, (actor_id,))
        result = cursor.fetchone()

        count = result['count'] if isinstance(result, dict) else result[0]

        if count == 0:
            sql = """
            INSERT INTO actors (id, name, img_url)
            VALUES (%s, %s, %s)
            """
            cursor.execute(sql, (actor_id, actor_name, img_url))
            connection.commit()
        else:
            print(f"Actor with id {actor_id} already exists.")
            connection.commit()
            return


def insert_genre(connection, genre_id, genre_name="Unknown")->None:
    with connection.cursor() as cursor:
        sql = """
        INSERT IGNORE INTO genres (id, name)
        VALUES (%s, %s)
        """
        cursor.execute(sql, (genre_id, genre_name))
    connection.commit()



def insert_movie_actor(connection, movie_id, actor_id) -> None:
    try:
        with connection.cursor() as cursor:
            check_sql = """
            SELECT COUNT(*) AS count 
            FROM movie_actors 
            WHERE movie_id = %s AND actor_id = %s
            """
            cursor.execute(check_sql, (movie_id, actor_id))
            result = cursor.fetchone()

            count = result['count'] if isinstance(result, dict) else result[0]

            if count == 0:
                sql = """
                INSERT INTO movie_actors (movie_id, actor_id)
                VALUES (%s, %s)
                """
                cursor.execute(sql, (movie_id, actor_id))
                connection.commit()
                print(f"Inserted movie_id {movie_id} and actor_id {actor_id} into movie_actors.")
            else:
                print(f"The pairing movie_id {movie_id} and actor_id {actor_id} already exists.")
    except Exception as e:
        print(f"An error occurred: {e}")



def link_movie_producers(connection, movie_id)->None:
    movie_details = get_movie_details(movie_id)
    if not movie_details:
        return
    producers = movie_details.get('production_companies', [])
    for producer in producers:
        producer_id = producer['id']
        producer_name = producer['name']
        
        insert_producer(connection, producer_id, producer_name)


def insert_all_genres(connection)->None:
    genres = get_genres()
    print(genres)
    for genre in genres:
        insert_genre(connection, genre['id'], genre['name'])

def main():
    connection = get_db_connection(app) 
    print("Adding genres...")
    insert_all_genres(connection)

    print("Fetching movies...")
    movies_data = get_movies(page=1)
      

    if movies_data:
        print("Adding producers...")
        for movie in movies_data['results']:
            try:
                link_movie_producers(connection, movie['id'])
            except Exception as e:
                print(f"Error adding producers for movie {movie['id']}: {e}")

            print("Adding movies and actors...")
            for movie in movies_data['results']:
                insert_movie(connection, movie)
            
            for movie in movies_data['results']:

                cast = get_movie_cast(movie['id'])
                for actor in cast:
                    actor_id = actor.get('id')
                    actor_name = actor.get('name')
                    img_url = actor.get('profile_path', None)

                    if actor_id and actor_name:
                        insert_actor(connection, actor_id, actor_name, img_url)
                        insert_movie_actor(connection, movie['id'], actor_id)
    
    connection.close()


if __name__ == "__main__":
    main()

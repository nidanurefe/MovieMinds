from app import createApp
from flask import render_template, request, jsonify
from flask import current_app as app

app = createApp()

@app.route('/')
def index():
    cursor = app.db.cursor()  # Standart cursor
    cursor.execute("""
        SELECT 
            movies.title, 
            movies.release_year, 
            movies.rating, 
            movies.cover_image,
            genres.name AS genre_name,
            producers.name AS producer_name
        FROM movies
        JOIN genres ON movies.genre_id = genres.id
        JOIN producers ON movies.producer_id = producers.id
    """)
    columns = [col[0] for col in cursor.description]  
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()]  # Convert into dict
    cursor.close()
    return render_template('index.html', movies=movies)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            cursor = app.db.cursor()
            cursor.execute(
                "INSERT INTO users (username, password, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)",
                (username, password, email, first_name, last_name))
            app.db.commit()
            cursor.close()
            return jsonify({"message": "User added successfully!"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            cursor = app.db.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()
            cursor.close()
            if user:
                return jsonify({"message": "Login successful!"}), 200
            else:
                return jsonify({"error": "Invalid credentials"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    return render_template('login.html')

@app.route('/favourite_actor', methods=['POST'])
def favourite_actor() -> tuple:
    try:
        actor_id = request.form['actor_id']
        user_id = request.form['user_id']
        cursor = app.db.cursor()
        cursor.execute(
            "INSERT INTO user_favorite_actors (user_id, actor_id) VALUES (%s, %s)",
            (user_id, actor_id))
        app.db.commit()
        cursor.close()
        return jsonify({"message": "Actor added to favourites!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/add_favourite', methods=['POST'])
def add_favourite():
    try:
        data = request.get_json()
        movie_id = data['movie_id']
        user_id = data['user_id']

        cursor = app.db.cursor()
        cursor.execute(
            "INSERT INTO user_favorites (user_id, movie_id) VALUES (%s, %s)",
            (user_id, movie_id)
        )
        app.db.commit()
        cursor.close()

        return jsonify({"message": "Movie added to favourites!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/rate_movie', methods=['POST'])
def rate_movie() -> tuple:
    try:
        movie_id = request.form['movie_id']
        user_id = request.form['user_id']
        review = request.form['review']
        rating = request.form['rating']

        cursor = app.db.cursor()
        cursor.execute(
            "INSERT INTO reviews (movie_id, user_id, review_text, rating) VALUES (%s, %s, %s, %s)",
            (movie_id, user_id, review, rating))
        app.db.commit()
        cursor.close()
        return jsonify({"message": "Movie rated successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/delete_review', methods=['POST'])
def delete_review() -> tuple:
    try:
        review_id = request.form['review_id']
        cursor = app.db.cursor()
        cursor.execute(
            "DELETE FROM reviews WHERE id = %s", (review_id,))
        app.db.commit()
        cursor.close()
        return jsonify({"message": "Review deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/add_movie', methods=['POST'])
def add_movie() -> tuple:
    try: 
        title = request.form['title']
        release_year = request.form['release_year']
        rating = request.form['rating']
        genre_id = request.form['genre_id']
        cover_image = request.form['cover_image']
        producer_id = request.form['producer_id']

        cursor = app.db.cursor()
        cursor.execute(
            "INSERT INTO movies (title, rating, release_year, genre_id, cover_image, producer_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (title, rating, release_year, genre_id, cover_image, producer_id))
        app.db.commit()
        cursor.close()
        return jsonify({"message": "Movie added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)

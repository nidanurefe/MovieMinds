from app import createApp
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = createApp()
app.secret_key = "your_secret_key"

@app.route('/', methods=['GET', 'POST'])
def index():
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))
    search_query = request.args.get('search', '')  # Arama kelimesi
    genre_filter = request.args.get('genre', '')   # Seçilen kategori

    cursor = app.db.cursor()
    cursor.execute("SELECT id, name FROM genres")
    genres = cursor.fetchall()

    # SQL sorgusunu oluştur
    query = """
        SELECT 
            movies.id,
            movies.title, 
            movies.release_year, 
            movies.rating, 
            movies.cover_image,
            genres.name AS genre_name,
            producers.name AS producer_name
        FROM movies
        JOIN genres ON movies.genre_id = genres.id
        JOIN producers ON movies.producer_id = producers.id
    """
    
    filters = []
    if search_query:
        query += " WHERE movies.title LIKE %s"
        filters.append(f'%{search_query}%')
    if genre_filter:
        query += " AND movies.genre_id = %s" if search_query else " WHERE movies.genre_id = %s"
        filters.append(genre_filter)

    cursor.execute(query, tuple(filters))
    columns = [col[0] for col in cursor.description]
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    return render_template('index.html', movies=movies, genres=genres, search_query=search_query, genre_filter=genre_filter)

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
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                flash("Username or email already exists. Please choose a different one.", "error")
                return render_template('register.html')

            cursor.execute(
                "INSERT INTO users (username, password, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)",
                (username, password, email, first_name, last_name))
            app.db.commit()
            cursor.close()

            return redirect(url_for('index'))

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
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()  

            if user:
                user_dict = {
                    'id': user[0],
                    'username': user[1],
                    'password': user[2],
                    'email': user[3],
                }
                session['user_id'] = user_dict['id']
                return redirect(url_for('index'))
            else:
                flash("Invalid credentials. User not found.", "error")
                return render_template('login.html')

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Kullanıcıyı session'dan çıkar
    return redirect(url_for('login'))


# Route to display user's favorite actors
@app.route('/fav-actors')
def favourite_actors():
    user_id = session.get('user_id')

    if not user_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('login'))

    # Kullanıcıya ait favori oyuncuları çek
    cursor = app.db.cursor()
    cursor.execute("""
        SELECT 
            actors.id,
            actors.name 
        FROM actors
        JOIN user_favorite_actors ON actors.id = user_favorite_actors.actor_id
        WHERE user_favorite_actors.user_id = %s
    """, (user_id,))
    columns = [col[0] for col in cursor.description]
    actors = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    return render_template('favourite-actors.html', actors=actors)


# Route to handle adding favorite actors
@app.route('/add_favorite_actor', methods=['POST'])
def add_favorite_actor():
    try:
        actor_id = request.form['actor_id']
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"error": "User not logged in."}), 401  # Kullanıcı giriş yapmamışsa hata döndür

        cursor = app.db.cursor()
        cursor.execute(
            "INSERT INTO user_favorite_actors (user_id, actor_id) VALUES (%s, %s)",
            (user_id, actor_id)
        )
        app.db.commit()
        cursor.close()

        return jsonify({"message": "Actor added to favorites!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/add_favourite', methods=['POST'])
def add_favourite():
    try:
        data = request.get_json()
        movie_id = data['movie_id']
        
        user_id = session.get('user_id')

        if not user_id:
            return jsonify({"error": "User not logged in."}), 401  # Kullanıcı giriş yapmamışsa hata döndür

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

@app.route('/fav-movies')
def favourite_movies():
    user_id = session.get('user_id')

    if not user_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('login'))

    cursor = app.db.cursor()
    cursor.execute("""
        SELECT 
            movies.id,
            movies.title, 
            movies.release_year, 
            movies.rating, 
            movies.cover_image,
            genres.name AS genre_name,
            producers.name AS producer_name
        FROM movies
        JOIN user_favorite_movies ON movies.id = user_favorite_movies.movie_id
        JOIN genres ON movies.genre_id = genres.id
        JOIN producers ON movies.producer_id = producers.id
        WHERE user_favorite_movies.user_id = %s
    """, (user_id,))
    columns = [col[0] for col in cursor.description]
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    return render_template('favourite-movies.html', movies=movies)


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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session.get('user_id')

    if not user_id:
        flash("You need to log in first.", "error")
        return redirect(url_for('login'))

    cursor = app.db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        flash("User not found.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            first_name = request.form['first_name']
            last_name = request.form['last_name']

            cursor.execute("""
                UPDATE users 
                SET username = %s, password = %s, email = %s, first_name = %s, last_name = %s 
                WHERE id = %s
            """, (username, password, email, first_name, last_name, user_id))
            app.db.commit()
            cursor.close()

            return redirect(url_for('profile'))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")

    return render_template('profile.html', user=user)

@app.route('/top-actors')
def top_actors():
    cursor = app.db.cursor()
    cursor.execute("""
        SELECT actors.id, actors.name, COUNT(user_favorite_actors.actor_id) AS fav_count
        FROM actors
        JOIN user_favorite_actors ON actors.id = user_favorite_actors.actor_id
        GROUP BY actors.id
        ORDER BY fav_count DESC
        LIMIT 10
    """)
    columns = [col[0] for col in cursor.description]
    actors = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    return render_template('top-actors.html', actors=actors)


@app.route('/top-movies')
def top_movies():
    cursor = app.db.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                movies.id,
                movies.title, 
                movies.release_year, 
                movies.rating, 
                movies.cover_image,
                genres.name AS genre_name,
                producers.name AS producer_name,
                COUNT(user_favorite_movies.movie_id) AS fav_count
            FROM movies
            JOIN genres ON movies.genre_id = genres.id
            JOIN producers ON movies.producer_id = producers.id
            LEFT JOIN user_favorite_movies ON movies.id = user_favorite_movies.movie_id
            GROUP BY movies.id, genres.name, producers.name
            ORDER BY fav_count DESC
            LIMIT 10
            """
        )
        
        if cursor.description:  # Ensure description is not None
            columns = [col[0] for col in cursor.description]
            movies = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            movies = []

    except Exception as e:
        app.logger.error(f"Database query failed: {e}")
        movies = []  # Fallback to an empty list on error

    finally:
        cursor.close()

    return render_template('top-movies.html', movies=movies)

@app.route('/show-session-id')
def show_session_id():
    session_id = session.sid if hasattr(session, 'sid') else "Session ID not available"
    return f"Current Session ID: {session_id}"

if __name__ == '__main__':
    app.run(debug=True)

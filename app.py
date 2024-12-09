from app import createApp
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = createApp()
app.secret_key = "your_secret_key"

def login_required(f):
    """Decorator to ensure user is logged in."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    search_query = request.args.get('search', '')  # Arama kelimesi
    genre_filter = request.args.get('genre', '')   # Seçilen kategori

    cursor = app.db.cursor()
    cursor.execute("SELECT id, name FROM genres")
    genres = cursor.fetchall()

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
        username = request.form['username']
        password = request.form['password']

        cursor = app.db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Please try again.", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))


@app.route('/fav-actors')
@login_required
def favourite_actors():
    user_id = session['user_id']

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
@login_required
def profile():
    user_id = session['user_id']

    cursor = app.db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
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

        flash("Profile updated successfully!", "success")
        return redirect(url_for('profile'))

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




@app.route('/edit_review/<int:review_id>', methods=['GET', 'POST'])
def edit_review(review_id):
    if request.method == 'POST':
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"error": "User not logged in."}), 401

            review_text = request.form['review_text']
            rating = request.form['rating']

            cursor = app.db.cursor()
            cursor.execute(
                "UPDATE reviews SET review_text = %s, rating = %s WHERE id = %s AND user_id = %s",
                (review_text, rating, review_id, user_id)
            )
            app.db.commit()
            cursor.close()

            return jsonify({"message": "Review updated successfully!"}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    cursor = app.db.cursor()
    cursor.execute(
        "SELECT review_text, rating FROM reviews WHERE id = %s AND user_id = %s",
        (review_id, session.get('user_id'))
    )
    review = cursor.fetchone()
    cursor.close()

    return render_template('edit-review.html', review=review, review_id=review_id)




@app.route('/reviews/all')
def review_all():
    cursor = app.db.cursor()

    cursor.execute("""
        SELECT 
            reviews.id,
            users.username AS user,
            movies.title AS movie,
            reviews.review_text 
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        JOIN movies ON reviews.movie_id = movies.id
    """)
    columns = [col[0] for col in cursor.description]
    reviews = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    return render_template('all-reviews.html', reviews=reviews)

@app.route('/show-session-id')
def show_session_id():
    session_id = session.sid if hasattr(session, 'sid') else "Session ID not available"
    return f"Current Session ID: {session_id}"

@app.route('/review/add', methods=['GET', 'POST'])
def add_review():
    if request.method == 'POST':
        movie = request.form.get('movie')
        review = request.form.get('review')
        user = "current_user"  # Mevcut oturumdaki kullanıcı adı (yerine gerçek kullanıcı doğrulaması eklenecek)
        review_id = len(reviews) + 1
        reviews.append({'id': review_id, 'user': user, 'movie': movie, 'review': review})
        return redirect(url_for('my_reviews'))
    return render_template('add-review.html')

from flask import session, render_template

@app.route('/reviews/my-reviews')
def my_reviews():
    if 'user_id' not in session:
        return redirect('/login')  # Kullanıcı giriş yapmamışsa login sayfasına yönlendirin
    
    user_id = session['user_id']  # Giriş yapan kullanıcının ID'sini alın
    cursor = app.db.cursor()

    # Giriş yapan kullanıcıya ait yorumları al
    cursor.execute("""
        SELECT 
            reviews.id,
            movies.title AS movie,
            reviews.review_text 
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.id
        WHERE reviews.user_id = %s
    """, (user_id,))
    
    columns = [col[0] for col in cursor.description]
    user_reviews = [dict(zip(columns, row)) for row in cursor.fetchall()]
    cursor.close()

    return render_template('my-reviews.html', reviews=user_reviews)



if __name__ == '__main__':
    app.run(debug=True)

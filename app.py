from functools import wraps
from app import createApp
from flask import render_template, request, redirect, url_for, flash, session, jsonify, make_response
import bcrypt, jwt, datetime


app = createApp() 
app.secret_key = "your_secret_key"


# Function to generate a JWT token for a given user ID
def generate_token(user_id):
    payload = {
        'user_id': user_id,  # Include the user ID in the payload
        'exp': datetime.datetime.now() + datetime.timedelta(hours=1)  # Set token expiration to 1 hour
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')  # Encode the payload with a secret key using HS256 algorithm
    return token  # Return the generated token


# Decorator to ensure that the user is authenticated via a valid token
def token_required(f):
    @wraps(f)  # Preserve the original function's attributes
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('auth_token')  # Retrieve the token from cookies
        if not token:  # If no token is found, return an error response
            print("No token found in request cookies")  # Debugging message
            return jsonify({"error": "Token is missing!"}), 401  # Return a 401 Unauthorized error

        try:
            # Decode the token using the secret key and validate it
            decoded_token = jwt.decode(token, app.secret_key, algorithms=['HS256'])
            print(f"Decoded token: {decoded_token}")  # Debugging message to show the decoded token
            request.user_id = decoded_token['user_id']  # Store the user ID in the request context
        except jwt.ExpiredSignatureError:  # Handle the case where the token has expired
            print("Token has expired")  # Debugging message
            return jsonify({"error": "Token has expired!"}), 401  # Return a 401 Unauthorized error
        except jwt.InvalidTokenError:  # Handle the case where the token is invalid
            print("Invalid token")  # Debugging message
            return jsonify({"error": "Invalid token!"}), 401  # Return a 401 Unauthorized error

        # If the token is valid, proceed with the original function
        return f(*args, **kwargs)
    return decorated_function


# Root route
@app.route('/', methods=['GET', 'POST'])
def index():
    # If user is not logged in, redirect to login page
    if 'user_id' not in session:
        return redirect(url_for('login'))
    search_query = request.args.get('search', '')  # Search query
    genre_filter = request.args.get('genre', '')   # Genre filter

    cursor = app.db.cursor() # Create a cursor
    cursor.execute("SELECT id, name FROM genres") # Fetch all genres
    genres = cursor.fetchall() # Fetch all genres

    # Query to fetch movies with genre and producer names
    query = """
        SELECT 
            movies.tmdb_id,
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
    
    filters = [] # Filters list
    if search_query: # If search query is provided
        query += " WHERE movies.title LIKE %s" # Add WHERE clause
        filters.append(f'%{search_query}%') # Append search query to filters list
    if genre_filter: # If genre filter is provided
        query += " AND movies.genre_id = %s" if search_query else " WHERE movies.genre_id = %s" # Add WHERE or AND clause
        filters.append(genre_filter) # Append genre filter to filters list

    cursor.execute(query, tuple(filters)) # Execute the query with filters
    columns = [col[0] for col in cursor.description] # Get column names
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all movies
    cursor.close() # Close the cursor
 
    return render_template('index.html', movies=movies, genres=genres, search_query=search_query, genre_filter=genre_filter) # Render the template with movies and genres

# ********** Routes for authorization **********


@app.route('/register', methods=['GET', 'POST']) # Route to register a new user
def register():
    if request.method == 'POST': # If the request method is POST
        try:
            username = request.form['username'] # Get username from form
            password = request.form['password'] # Get password from form
            email = request.form['email'] # Get email from form
            first_name = request.form['first_name'] # Get first name from form
            last_name = request.form['last_name'] # Get last name from form

            cursor = app.db.cursor() # Create a cursor
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email)) # Check if user exists
            existing_user = cursor.fetchone() # Fetch the user

            if existing_user: # If user exists
                flash("Username or email already exists. Please choose a different one.", "error") # Flash an error message
                return render_template('register.html') # Render the register template
            # hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) # Hash the password

            cursor.execute( # Execute the query to insert the user
                "INSERT INTO users (username, password, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)", 
                (username, hashed_password, email, first_name, last_name))
            app.db.commit() # Commit the changes
            cursor.close() # Close the cursor

            return redirect(url_for('index')) # Redirect to the index page

        except Exception as e: # If an exception occurs
            return jsonify({"error": str(e)}), 400 # Return an error message

    return render_template('register.html') # Render the register template

@app.route('/login', methods=['GET', 'POST']) # Route to login
def login(): 
    if request.method == 'POST': # If the request method is POST
        username = request.form['username'] # Get username from form
        password = request.form['password'] # Get password from form
 
        cursor = app.db.cursor() # Create a cursor
        cursor.execute("SELECT id, username, password FROM users WHERE username = %s", (username,)) # Check if user exists

        user = cursor.fetchone() # Fetch the user

        if user: # If user exists 
            stored_password = user[2] # Veritabanında saklanan hashlenmiş şifre
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')): # Şifreyi doğrula
                session['user_id'] = user[0] # Set the user ID in the session
                session['username'] = user[1] # Set the username in the session
                token = generate_token(user[0])
                response = make_response(redirect('/'))
                response.set_cookie('auth_token', token, httponly=True, secure=False)
                return response
            else:
                flash("Invalid credentials. Please try again.", "error") # Flash an error message
        else: # If user does not exist
            flash("Invalid credentials. Please try again.", "error") # Flash an error message


    return render_template('login.html') # If the request method is GET Render the login template 

@app.route('/logout') # Route to logout
def logout(): 
    session.clear() # Clear the session 
    return redirect(url_for('login')) # Redirect to the login page


# ********** ROUTES FOR ACTORS  **********

@app.route('/fav-actors') # Route to get user's favourite actors
@token_required
def favourite_actors(): 
    user_id = session['user_id'] # Get the user ID from the session

    cursor = app.db.cursor() # Create a cursor
    # Query to get the user's favourite actors
    cursor.execute(""" 
        SELECT 
            actors.id,
            actors.name,
            actors.img_url  
        FROM actors
        JOIN user_favorite_actors ON actors.id = user_favorite_actors.actor_id
        WHERE user_favorite_actors.user_id = %s
    """, (user_id,))
    
    columns = [col[0] for col in cursor.description] # Get column names
    actors = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all actors
    cursor.close() # Close the cursor

    return render_template('favourite-actors.html', actors=actors) # Render the template with actorsß



@app.route('/add_favorite_actor', methods=['POST']) # Route to add a favourite actor
@token_required 
def add_favorite_actor():
    data = request.get_json() # Get the JSON data
    actor_id = data.get('actor_id') # Get the actor ID
    user_id = session.get('user_id') # Get the user ID from the session

    if not user_id: # If user is not logged in
        return jsonify({"error": "User not logged in."}), 401 # Return an error message

    try: # Try to add the actor to favourites
        cursor = app.db.cursor() # Create a cursor

        # Check if the actor is already in favourites
        cursor.execute(
            "SELECT COUNT(*) FROM user_favorite_actors WHERE user_id = %s AND actor_id = %s",
            (user_id, actor_id)
        )

        
        if cursor.fetchone()[0] > 0:  # If the actor is already in favourites
            return jsonify({"message": "Actor is already in your favorites!"}), 200 # Return a message

        # Add the actor to favourites
        cursor.execute(
            "INSERT INTO user_favorite_actors (user_id, actor_id) VALUES (%s, %s)",
            (user_id, actor_id)
        )
        
        app.db.commit() # Commit the changes
        cursor.close() # Close the cursor

        return jsonify({"message": "Actor added to favorites!"}), 200 # Return a message
 
    except Exception as e: # If an exception occurs
        return jsonify({"error": str(e)}), 400  # Return an error message


@app.route('/top-actors') # Route to get top actors
@token_required 
def top_actors(): 
    cursor = app.db.cursor() # Create a cursor
    # Query to get top actors
    cursor.execute("""
        SELECT actors.id, actors.name, actors.img_url, 
               COUNT(user_favorite_actors.actor_id) AS fav_count
        FROM actors
        LEFT JOIN user_favorite_actors 
        ON actors.id = user_favorite_actors.actor_id
        GROUP BY actors.id
        ORDER BY fav_count DESC
    """)

    columns = [col[0] for col in cursor.description] # Get column names
    actors = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all actors
    cursor.close() # Close the cursor
 
    return render_template('top-actors.html', actors=actors) # Render the template with actors

@app.route('/remove_favorite_actor', methods=['POST']) # Route to remove a favourite actor
@token_required 
def remove_favorite_actor(): 
    try: # Try to remove the actor from favourites
        data = request.get_json() # Get the JSON data
        actor_id = data.get('actor_id') # Get the actor ID
        user_id = session.get('user_id') # Get the user ID from the session

        if not user_id: # If user is not logged in
            return jsonify({"error": "User not logged in."}), 401 # Return an error message

        cursor = app.db.cursor() # Create a cursor

        # Delete the actor from favourites
        cursor.execute(
            "DELETE FROM user_favorite_actors WHERE user_id = %s AND actor_id = %s",
            (user_id, actor_id)
        )
        app.db.commit() # Commit the changes
        cursor.close() # Close the cursor
 
        return jsonify({"message": "Actor removed from favorites!"}), 200 # Return a message

    except Exception as e: # If an exception occurs
        return jsonify({"error": str(e)}), 400 # Return an error message


# ********* ROUTES FOR MOVIES *********

@app.route('/add_favourite', methods=['POST']) # Route to add a favourite movie
@token_required 
def add_favourite():  
    if 'user_id' not in session: # If user is not logged in
        return jsonify({"error": "User not logged in"}), 401 # Return an error message

    user_id = session['user_id'] # Get the user ID from the session
    movie_id = request.json.get('movie_id') # Get the movie ID from the request

    if not movie_id: # If movie ID is not provided
        return jsonify({"error": "Movie ID is required"}), 400 # Return an error message

    try:
        cursor = app.db.cursor() # Create a cursor
        # Check if already in favourites
        cursor.execute("SELECT * FROM user_favorite_movies WHERE user_id = %s AND movie_id = %s", (user_id, movie_id))
        if cursor.fetchone(): # If movie is already in favourites
            return jsonify({"message": "Movie already in favourites"}), 200 # Return a message

        # Add to favourites
        cursor.execute("INSERT INTO user_favorite_movies (user_id, movie_id) VALUES (%s, %s)", (user_id, movie_id))
        app.db.commit() # Commit the changes
        return jsonify({"message": "Movie added to favourites"}), 201 # Return a message
    except Exception as e: # If an exception occurs
        return jsonify({"error": str(e)}), 500 # Return an error message


@app.route('/fav-movies')  # Route to get user's favourite movies
@token_required 
def favourite_movies(): 
    user_id = session.get('user_id') # Get the user ID from the session

    if not user_id: # If user is not logged in
        return redirect(url_for('login')) # Redirect to the login page

    cursor = app.db.cursor() # Create a cursor

    # Query to get the user's favourite movies
    cursor.execute("""
        SELECT 
            movies.tmdb_id,
            movies.title, 
            movies.release_year, 
            movies.rating, 
            movies.cover_image,
            genres.name AS genre_name,
            producers.name AS producer_name
        FROM movies
        JOIN user_favorite_movies ON movies.tmdb_id = user_favorite_movies.movie_id
        JOIN genres ON movies.genre_id = genres.id
        JOIN producers ON movies.producer_id = producers.id
        WHERE user_favorite_movies.user_id = %s
    """, (user_id,))

    columns = [col[0] for col in cursor.description] # Get column names
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all movies
    cursor.close() # Close the cursor

    return render_template('favourite-movies.html', movies=movies) # Render the template with movies


@app.route('/remove_favourite', methods=['POST']) # Route to remove a favourite movie
@token_required 
def remove_favourite(): 
    user_id = session.get('user_id') # Get the user ID from the session

    if not user_id: # If user is not logged in
        return jsonify({"error": "You must be logged in to remove favourites."}), 401 # Return an error message

    try:
        data = request.get_json() # Get the JSON data
        movie_id = data.get('movie_id') # Get the movie ID

        if not movie_id: # If movie ID is not provided
            return jsonify({"error": "Movie ID is required."}), 400 # Return an error message

        cursor = app.db.cursor() # Create a cursor
    

        # Delete the movie from favourites
        cursor.execute(""" 
            DELETE FROM user_favorite_movies 
            WHERE user_id = %s AND movie_id = %s
        """, (user_id, movie_id))


        app.db.commit() # Commit the changes
        cursor.close() # Close the cursor

        return jsonify({"message": "Movie removed from favourites successfully."}) # Return a message
    
    except Exception as e: # If an exception occurs
        app.db.rollback() # Rollback the changes
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500 # Return an error message


@app.route('/top-movies') # Route to get top movies
@token_required 
def top_movies(): 
    cursor = app.db.cursor()  # Create a cursor
    try: # Try to get the top movies
        # Query to get top movies
        cursor.execute(
            """
            SELECT 
                movies.tmdb_id,
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
            LEFT JOIN user_favorite_movies ON movies.tmdb_id = user_favorite_movies.movie_id
            GROUP BY movies.tmdb_id, genres.name, producers.name
            ORDER BY fav_count DESC
            LIMIT 24
            """
        )

        if cursor.description:  # Ensure description is not None
            columns = [col[0] for col in cursor.description] # Get column names
            movies = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all movies
        else:
            movies = [] # Fallback to an empty list if no movies are found

    except Exception as e: # If an exception occurs
        movies = []  # Fallback to an empty list on error

    finally:
        cursor.close() # Close the cursor

    return render_template('top-movies.html', movies=movies) # Render the template with movies


@app.route('/get_movies_by_actor/<int:actor_id>') # Route to get movies by actor
@token_required
def get_movies_by_actor(actor_id):
    try:
        cursor = app.db.cursor() # Create a cursor
        cursor.execute(""" 
            SELECT movies.tmdb_id, movies.title, movies.cover_image, movies.release_year AS year
            FROM movies
            JOIN movie_actors ON movies.tmdb_id = movie_actors.movie_id
            WHERE movie_actors.actor_id = %s
        """, (actor_id,))
        movies = [{"id": row[0], "title": row[1], "cover_image": row[2], "year": row[3]} for row in cursor.fetchall()] # Fetch all movies
        cursor.close()  # Close the cursor
        return jsonify({"movies": movies}) # Return the movies
    except Exception as e:
        return jsonify({"error": str(e)}), 500 # Return an error message


@app.route('/get_actors/<int:movie_id>') # Route to get actors in a movie
@token_required 
def get_actors(movie_id):
    cursor = app.db.cursor() # Create a cursor
    cursor.execute("""
        SELECT actors.name, actors.img_url
        FROM actors
        JOIN movie_actors ON actors.id = movie_actors.actor_id
        WHERE movie_actors.movie_id = %s
    """, (movie_id,))
    actors = [{"name": row[0], "img_url": row[1]} for row in cursor.fetchall()] # Fetch all actors
    cursor.close() # Close the cursor
    return jsonify({"actors": actors}) # Return the actors

# ********** ROUTES FOR PROFILE **********

@app.route('/profile', methods=['GET', 'POST']) # Route to view and edit user profile
@token_required # Ensure user is logged in
def profile(): 
    user_id = session['user_id'] # Get the user ID from the session

    cursor = app.db.cursor() # Create a cursor
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,)) # Get the user details
    user = cursor.fetchone() # Fetch the user
 
    if request.method == 'POST': # If the request method is POST
        username = request.form['username'] # Get the username from the form
        password = request.form['password'] # Get the password from the form
        email = request.form['email'] # Get the email from the form
        first_name = request.form['first_name'] # Get the first name from the form
        last_name = request.form['last_name'] # Get the last name from the form
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) # Hash the password

        # Update the user details
        cursor.execute("""
            UPDATE users 
            SET username = %s, password = %s, email = %s, first_name = %s, last_name = %s 
            WHERE id = %s
        """, (username, hashed_password, email, first_name, last_name, user_id))
        app.db.commit() # Commit the changes
        cursor.close() # Close the cursor

        return redirect(url_for('profile')) # Redirect to the profile page

    return render_template('profile.html', user=user) # Render the template with user details




# ******* ROUTES FOR REVIEWS ********


@app.route('/reviews/all', methods=['GET', 'POST']) # Route to view all reviews
@token_required 
def review_all(): 
    cursor = app.db.cursor() # Create a cursor

    # Get all movies
    cursor.execute("""
        SELECT tmdb_id, title FROM movies
    """)
    columns = [col[0] for col in cursor.description]
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()]

    #  Get all reviews
    cursor.execute("""
        SELECT 
            reviews.id,
            users.username AS user,
            movies.title AS movie,
            reviews.review_text,
            movies.cover_image AS cover_image  
        FROM reviews
        JOIN users ON reviews.user_id = users.id
        JOIN movies ON reviews.movie_id = movies.tmdb_id
    """)
    columns = [col[0] for col in cursor.description] # Get column names
    reviews = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all reviews
    cursor.close() # Close the cursor
 
    return render_template('all-reviews.html', reviews=reviews, movies=movies) # Render the template with reviews and movies


@app.route('/review/add', methods=['GET', 'POST']) # Route to add a review
@token_required 
def add_review(): 
    user_id = session.get('user_id') # Get the user ID from the session
    
    if not user_id: # If user is not logged in
        return redirect('/login')  # Redirect to the login page

    if request.method == 'POST': # If the request method is POST
        movie_id = request.form.get('movie_id') # Get the movie ID from the form
        review = request.form.get('review') # Get the review from the form
        rating = request.form.get('rating') # Get the rating from the form
        if not movie_id or not review: # If movie ID or review is not provided
            return render_template('add_review.html', error="All fields are required.", movies=fetch_movies()) # Render the template with an error message

        try:
            cursor = app.db.cursor() # Create a cursor

            # Create a review
            cursor.execute(
                """
                INSERT INTO reviews (user_id, movie_id, review_text, rating) 
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, movie_id, review, rating)
            )

            # Fetch existing rating from movies table
            cursor.execute(
                """
                SELECT rating FROM movies WHERE tmdb_id = %s
                """, (movie_id)
            )
            tmdb_rating = cursor.fetchone()[0] 

            # Calculate averate user rating for the movie
            cursor.execute(
                """
                SELECT AVG(rating) FROM reviews WHERE movie_id = %s
                """, (movie_id,)
            )
            average_user_rating = cursor.fetchone()[0]  

            combined_rating:float = (tmdb_rating + average_user_rating) / 2

            # Update the movie's rating in the movies table
            cursor.execute(
                """
                UPDATE movies 
                SET rating = %s 
                WHERE tmdb_id = %s
                """, 
                (combined_rating, movie_id)
            )


            app.db.commit() # Commit the changes
            cursor.close()  # Close the cursor

            return redirect('/reviews/my-reviews')  # Redirect to the user's reviews
        except Exception as e: # If an exception occurs
            app.db.rollback()  # Rollback the changes
            return render_template('add-review.html', error=str(e), movies=fetch_movies()) # Render the template with an error message

    # GET request : Render the review form
    return render_template('add-review.html', movies=fetch_movies())


def fetch_movies():
    # Create a cursor
    cursor = app.db.cursor()

    try:
        # Select movies from the database
        cursor.execute("SELECT tmdb_id, title FROM movies")  
        movies = cursor.fetchall()  # Select movies from the database

        # Close the cursor
        cursor.close()

        return movies  # Return the movies
    except Exception as e: # If an exception occurs
        cursor.close() # Close the cursor
        return []  # Return an empty list


@app.route('/reviews/my-reviews') # Route to view user's reviews
@token_required 
def my_reviews():
    if 'user_id' not in session: # If user is not logged in
        return redirect('/login')  # Redirect to the login page
    
    user_id = session['user_id']  # Get the user ID from the session
    cursor = app.db.cursor() # Create a cursor

    # Get the user's reviews
    cursor.execute("""
        SELECT 
            reviews.id,
            movies.title AS movie,
            reviews.review_text, reviews.rating,
            movies.cover_image AS cover_image  
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.tmdb_id
        WHERE reviews.user_id = %s
    """, (user_id, ))
    
    columns = [col[0] for col in cursor.description] # Get column names
    user_reviews = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all reviews
    cursor.close() # Close the cursor
 
    return render_template('my-reviews.html', reviews=user_reviews) # Render the template with user's reviews


@app.route('/review/delete/<int:review_id>', methods=['GET']) # Route to delete a review
@token_required 
def delete_review(review_id): 
    if 'user_id' not in session: # If user is not logged in
        return redirect('/login')  # Redirect to the login page

    user_id = session['user_id'] # Get the user ID from the session
    cursor = app.db.cursor() # Create a cursor

    # Delete the review
    cursor.execute("""
        DELETE FROM reviews
        WHERE id = %s AND user_id = %s
    """, (review_id, user_id))
    app.db.commit() # Commit the changes

    cursor.close() # Close the cursor
    return redirect('/reviews/my-reviews')  # Redirect to the user's reviews

@app.route('/review/edit/<int:review_id>', methods=['GET', 'POST']) # Route to edit a review
@token_required 
def edit_review(review_id): 
    if 'user_id' not in session: # If user is not logged in
        return redirect('/login')  # Redirect to the login page
    
    user_id = session['user_id'] # Get the user ID from the session
    cursor = app.db.cursor() # Create a cursor

    # Get the review to edit
    cursor.execute("""
        SELECT reviews.id, reviews.review_text, reviews.rating, movies.tmdb_id, movies.rating
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.tmdb_id
        WHERE reviews.id = %s AND reviews.user_id = %s
    """, (review_id, user_id))
    review = cursor.fetchone() # Fetch the review

    if not review:  # If review is not found
        return redirect('/reviews/my-reviews')  # Redirect to the user's reviews

    if request.method == 'POST': # If the request method is POST
        updated_review = request.form['review_text'] # Get the updated review
        updated_rate = request.form['rating']
        movie_id = review[3]
        tmdb_rating = review[4]
        # Update the review
        cursor.execute("""
            UPDATE reviews
            SET review_text = %s, rating = %s
            WHERE id = %s
        """, (updated_review, updated_rate, review_id))

        cursor.execute("""
            SELECT AVG(rating) FROM reviews WHERE movie_id = %s
        """, (movie_id,))
        average_user_rating = cursor.fetchone()[0]
        combined_rating = (tmdb_rating + average_user_rating) / 2

        cursor.execute("""
            UPDATE movies 
            SET rating = %s 
            WHERE tmdb_id = %s
        """, (combined_rating, movie_id))

    

        app.db.commit() # Commit the changes
        cursor.close()

        return redirect('/reviews/my-reviews')  # Redirect to the user's reviews

    cursor.close() # Close the cursor
    return render_template('edit-review.html', review=review)  # Render the template with the review




if __name__ == '__main__':
    app.run(debug=True)

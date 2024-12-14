from app import createApp
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

app = createApp()
app.secret_key = "your_secret_key"


# Decorator to ensure user logged in
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first.", "error")
            return redirect(url_for('login'))
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

            cursor.execute( # Execute the query to insert the user
                "INSERT INTO users (username, password, email, first_name, last_name) VALUES (%s, %s, %s, %s, %s)", 
                (username, password, email, first_name, last_name))
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
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password)) # Check if user exists
        user = cursor.fetchone() # Fetch the user

        if user: # If user exists 
            session['user_id'] = user[0] # Set the user ID in the session
            session['username'] = user[1] # Set the username in the session
            return redirect(url_for('index')) # Redirect to the index page
        else: # If user does not exist
            flash("Invalid credentials. Please try again.", "error") # Flash an error message

    return render_template('login.html') # If the request method is GET Render the login template 

@app.route('/logout') # Route to logout
def logout(): 
    session.clear() # Clear the session 
    return redirect(url_for('login')) # Redirect to the login page


# ********** ROUTES FOR ACTORS  **********

@app.route('/fav-actors') # Route to get user's favourite actors
@login_required 
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
@login_required 
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
@login_required 
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
@login_required 
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
@login_required 
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
@login_required 
def favourite_movies(): 
    user_id = session.get('user_id') # Get the user ID from the session

    if not user_id: # If user is not logged in
        return redirect(url_for('login')) # Redirect to the login page

    cursor = app.db.cursor() # Create a cursor

    # Query to get the user's favourite movies
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

    columns = [col[0] for col in cursor.description] # Get column names
    movies = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all movies
    cursor.close() # Close the cursor

    return render_template('favourite-movies.html', movies=movies) # Render the template with movies


@app.route('/remove_favourite', methods=['POST']) # Route to remove a favourite movie
@login_required 
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
@login_required 
def top_movies(): 
    cursor = app.db.cursor()  # Create a cursor
    try: # Try to get the top movies
        # Query to get top movies
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
            LIMIT 8
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



# ********** ROUTES FOR PROFILE **********

@app.route('/profile', methods=['GET', 'POST']) # Route to view and edit user profile
@login_required # Ensure user is logged in
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
        
        # Update the user details
        cursor.execute("""
            UPDATE users 
            SET username = %s, password = %s, email = %s, first_name = %s, last_name = %s 
            WHERE id = %s
        """, (username, password, email, first_name, last_name, user_id))
        app.db.commit() # Commit the changes
        cursor.close() # Close the cursor

        return redirect(url_for('profile')) # Redirect to the profile page

    return render_template('profile.html', user=user) # Render the template with user details




# ******* ROUTES FOR REVIEWS ********


@app.route('/reviews/all', methods=['GET', 'POST']) # Route to view all reviews
@login_required 
def review_all(): 
    cursor = app.db.cursor() # Create a cursor

    # Get all movies
    cursor.execute("""
        SELECT id, title FROM movies
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
        JOIN movies ON reviews.movie_id = movies.id
    """)
    columns = [col[0] for col in cursor.description] # Get column names
    reviews = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all reviews
    cursor.close() # Close the cursor
 
    return render_template('all-reviews.html', reviews=reviews, movies=movies) # Render the template with reviews and movies


@app.route('/review/add', methods=['GET', 'POST']) # Route to add a review
@login_required 
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
        cursor.execute("SELECT id, title FROM movies")  
        movies = cursor.fetchall()  # Select movies from the database

        # Close the cursor
        cursor.close()

        return movies  # Return the movies
    except Exception as e: # If an exception occurs
        cursor.close() # Close the cursor
        return []  # Return an empty list


@app.route('/reviews/my-reviews') # Route to view user's reviews
@login_required 
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
            reviews.review_text,
            movies.cover_image AS cover_image  -- Poster resmini alıyoruz
        FROM reviews
        JOIN movies ON reviews.movie_id = movies.id
        WHERE reviews.user_id = %s
    """, (user_id, ))
    
    columns = [col[0] for col in cursor.description] # Get column names
    user_reviews = [dict(zip(columns, row)) for row in cursor.fetchall()] # Fetch all reviews
    cursor.close() # Close the cursor
 
    return render_template('my-reviews.html', reviews=user_reviews) # Render the template with user's reviews


@app.route('/review/delete/<int:review_id>', methods=['GET']) # Route to delete a review
@login_required 
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
@login_required 
def edit_review(review_id): 
    if 'user_id' not in session: # If user is not logged in
        return redirect('/login')  # Redirect to the login page
    
    user_id = session['user_id'] # Get the user ID from the session
    cursor = app.db.cursor() # Create a cursor

    # Get the review to edit
    cursor.execute("""
        SELECT id, review_text
        FROM reviews
        WHERE id = %s AND user_id = %s
    """, (review_id, user_id))
    review = cursor.fetchone() # Fetch the review

    if not review:  # If review is not found
        return redirect('/reviews/my-reviews')  # Redirect to the user's reviews

    if request.method == 'POST': # If the request method is POST
        updated_review = request.form['review_text'] # Get the updated review

        # Update the review
        cursor.execute("""
            UPDATE reviews
            SET review_text = %s
            WHERE id = %s
        """, (updated_review, review_id))
        app.db.commit() # Commit the changes

        return redirect('/reviews/my-reviews')  # Redirect to the user's reviews

    cursor.close() # Close the cursor
    return render_template('edit-review.html', review=review)  # Render the template with the review




if __name__ == '__main__':
    app.run(debug=True)

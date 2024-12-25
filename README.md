# Movie Review Platform

This project is a platform where users can rate and review movies. Below are the steps to set up and run the project.

## Getting Started

### 1. Database Connections

To set up the database connections, modify the database parameters in the `__init__.py` file. This file contains the necessary information to connect to the MySQL database. After updating the credentials, you can create the database using the provided SQL schema in the repository.

### 2. Database Schema

The database schema is included in the repository. The schema contains all the necessary tables and relationships. Use the provided SQL code to set up the MySQL database.

### 3. TMDB API Key

To fetch movie data from TMDB, you need to obtain an API key. Visit the [TMDB API](https://www.themoviedb.org/settings/api) page, create an account, and generate an API key.

Once you have the API key, create a `.env` file in the root directory of the project and add the following line:

```env
API_KEY=your_tmdb_api_key_here
```

### 4. Inserting Data into Database
After setting up the database, you can insert movie data from TMDB by calling the `insert_from_tmdb.py` file. You can specify the page to fetch from TMDB.

### 5. Runninng the Project
To start the project, run the `app.py` file.

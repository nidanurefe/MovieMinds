from flask import Flask
import pymysql


def createApp():
    app = Flask(__name__)

    app.config['MYSQL_HOST'] = '127.0.0.1'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'nido123'
    app.config['MYSQL_DB'] = 'movie_review_db'

    app.db = pymysql.connect(
        host = app.config['MYSQL_HOST'],
        user = app.config['MYSQL_USER'],
        password = app.config['MYSQL_PASSWORD'],
        db = app.config['MYSQL_DB'],
        
    )


    return app
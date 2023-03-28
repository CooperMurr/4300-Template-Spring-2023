import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = "S3Aledes"
MYSQL_PORT = 3306
MYSQL_DATABASE = "bookbeatsdb"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

# Sample search, the LIKE operator in this case is hard-coded,
# but if you decide to use SQLAlchemy ORM framework,
# there's a much better and cleaner way to do this
def sql_search(song):
    #inp = song.split(";", 1)
    #book = inp[0]
    #desc = inp[1]
    #x = ""
    #for word in desc.split():
        #x = x + "'%%" + word.lower() + "%%'" + " OR "
    #x = x[:-4]
    #query_sql = f"""SELECT * FROM songs WHERE LOWER( text ) LIKE {x} limit 10"""
    query_sql = f"""SELECT * FROM songs WHERE LOWER( text ) LIKE '%%{song.lower()}%%' limit 10"""
    keys = ["artist", "song", "link", "text"]
    data = mysql_engine.query_selector(query_sql)
    return json.dumps([dict(zip(keys, i)) for i in data])


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/songs")
def songs_search():
    text = request.args.get("title")
    ret = sql_search(text)
    return ret


app.run(debug=True)

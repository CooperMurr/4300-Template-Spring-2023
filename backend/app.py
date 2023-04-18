import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
import numpy as np
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from sklearn.feature_extraction.text import TfidfVectorizer

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = "^R4CQ3B%ArKTp*"
MYSQL_PORT = 3306
MYSQL_DATABASE = "bookbeatsdb"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()

app = Flask(__name__)
CORS(app)

def build_vectorizer(max_features, stop_words, max_df=0.8, min_df=5, norm='l2'):
    vectorizer = TfidfVectorizer(max_features=max_features, stop_words=stop_words, max_df=max_df, min_df=min_df, norm=norm)
    return vectorizer

def cos_search(song):
    n_feats = 5000
    tfidf_vec = build_vectorizer(n_feats, "english")
    lyric = mysql_engine.query_selector(f"""SELECT playlistname FROM songs""").fetchall()
   
    lyric.append(song)
    lyric =  [val[0] for val in lyric]
    lyric = [val for val in lyric if val is not None]

    lyric_by_vocab = tfidf_vec.fit_transform(lyric).toarray()
    lyric_idx_to_vocab = {i:v for i, v in enumerate(tfidf_vec.get_feature_names())}
    songlist = mysql_engine.query_selector(f"""SELECT trackname FROM songs""").fetchall()
    songlist =  [val[0] for val in songlist]
    songlist = [val for val in songlist if val is not None]
    #cosine similarity
    top = []
    d1 = lyric_by_vocab[-1]
    print(lyric_by_vocab)
    for n in range(0,len(lyric) - 1):
        d2 = lyric_by_vocab[n]
        sim = (np.dot(d1, d2))/(np.dot(np.linalg.norm(d1), np.linalg.norm(d2)))
        top.append((n, sim))
    top.sort(key = lambda tup: tup[1])
    print(top)
    #search dataset
    data = []
    keys = ["user_id", "artistname", "trackname", "playlistname"]
    for m in range(0, 10):
        query_sql = f"""SELECT * FROM songs WHERE trackname = {songlist[top[m][0]]} limit 1"""
        data.append(mysql_engine.query_selector(query_sql))
    print(data)
    return json.dumps([dict(zip(keys, i)) for i in data])

def sql_search(song):
    n_feats = 5000
    tfidf_vec = build_vectorizer(n_feats, "english")

    x = ""
    for word in song.split():
        x = x + "'%%" + word.lower() + "%%'" + " OR "
    x = x[:-4]
    #query_sql = f"""SELECT playlistname FROM songs"""
    query_sql = f"""SELECT * FROM songs WHERE LOWER( playlistname ) LIKE '%%{song.lower()}%%' limit 10"""
    keys = ["user_id", "artistname", "trackname", "playlistname"]
    data = mysql_engine.query_selector(query_sql)
    
    return json.dumps([dict(zip(keys, i)) for i in data])


@app.route("/")
def home():
    return render_template('base.html', title="sample html")


@app.route("/songs")
def songs_search():
    text = request.args.get("title")
    book = request.args.get("book")
    ret = sql_search(text)
    return ret


app.run(debug=True)

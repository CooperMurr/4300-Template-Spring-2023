import json
import os
from flask import Flask, render_template, request
from flask_cors import CORS
import numpy as np
from helpers.MySQLDatabaseHandler import MySQLDatabaseHandler
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse.linalg import svds
from sklearn.preprocessing import normalize
import math

# ROOT_PATH for linking with all your files.
# Feel free to use a config.py or settings.py with a global export variable
os.environ['ROOT_PATH'] = os.path.abspath(os.path.join("..", os.curdir))

# These are the DB credentials for your OWN MySQL
# Don't worry about the deployment credentials, those are fixed
# You can use a different DB name if you want to
MYSQL_USER = "root"
MYSQL_USER_PASSWORD = "nibroc25"
MYSQL_PORT = 3306
MYSQL_DATABASE = "bookbeatsdb"

mysql_engine = MySQLDatabaseHandler(
    MYSQL_USER, MYSQL_USER_PASSWORD, MYSQL_PORT, MYSQL_DATABASE)

# Path to init.sql file. This file can be replaced with your own file for testing on localhost, but do NOT move the init.sql file
mysql_engine.load_file_into_db()


app = Flask(__name__) 
CORS(app)

def build_vectorizer(max_features, stop_words, max_df=0.8, min_df=1, norm='l2'):
    vectorizer = TfidfVectorizer(max_features=max_features, stop_words=stop_words, max_df=max_df, min_df=min_df, norm=norm)
    return vectorizer

def svd(theme):
    n_feats = 5000
    vectorizer = build_vectorizer(n_feats,"english")
    
    lists = mysql_engine.query_selector(f"""SELECT playlistname FROM songs""").fetchall()
    names = [x[0] for x in lists if x[0] is not None]
    
    #svd
    td_mat = vectorizer.fit_transform([x for x in names])
    docs_compressed, s, words_compressed = svds(td_mat, k=100)
    words_compressed = words_compressed.transpose()

    word_to_index = vectorizer.vocabulary_
    index_to_word = {i:t for t,i in word_to_index.items()}

    words_compressed_normed = normalize(words_compressed, axis = 1)

    # cosine similarity
    def closest_words(word_in, words_representation_in, k = 10):
        if word_in not in word_to_index: return "No results"
        sims = words_representation_in.dot(words_representation_in[word_to_index[word_in],:])
        asort = np.argsort(-sims)[:k+1]
        return [(index_to_word[i],sims[i]) for i in asort[1:]]
    

    def query_exp(query):
        query_list = query.split()
        sz = len(query_list)
        num_closest = math.ceil((10-sz)/sz)

        closest_word_list = query_list
        
        for word in query_list:
            for w, sim in closest_words(word,words_compressed_normed):
                closest_word_list.append(w)
        
        return closest_word_list
    
    closest_word_list = query_exp(theme)

    #search
    data = []
    keys = ["user_id", "_artistname_", "_trackname_", "_playlistname_"]

    playlists_by_vocab = vectorizer.fit_transform(names).toarray()
    input_by_vocab = vectorizer.transform(closest_word_list).toarray()

    #cosine similarity
    top = []
    d1 = input_by_vocab[0]
    for d1 in input_by_vocab:
        for n in range(0,len(names)):
            d2 = playlists_by_vocab[n]
            numerator = (np.dot(d1,d2))
            denom = np.linalg.norm(d1) * np.linalg.norm(d2)
            sim = numerator/denom
            top.append((n, sim))

    top = sorted(top, key=lambda x: x[1], reverse=True)

    top = sorted(top, key=lambda x: x[1], reverse=True)
    #search dataset
    data = []
    keys = ["user_id", "_artistname_", "_trackname_", "_playlistname_"]
    
    for m in range(0, 10):
        if (top[m][0] != None):
            query_sql = f"""SELECT * FROM songs WHERE _playlistname_ = '{names[top[m][0]]}' limit 1"""
            data.append(mysql_engine.query_selector(query_sql))
        
    result_list = []
    for cursor in data: 
        for i in cursor: 
            result_list.append(dict(zip(keys,i)))
    
    return json.dumps(result_list)


def cos_search(song):
    if mysql_engine is None:
        return "Error: MySQL engine not intialized"
    
    n_feats = 5000
    tfidf_vec = build_vectorizer(n_feats, "english")

    playlistnames = mysql_engine.query_selector(f"""SELECT _playlistname_ FROM songs""").fetchall()
    playlistnames = [val[0] for val in playlistnames]
    playlistnames = [val for val in playlistnames if val is not None]

    #remove dupes while keeping order
    dupeless_names = {}
    for name in playlistnames:
        dupeless_names[name] = None #value is pointless, just using dict to remove dupes
    playlistnames = [key for key in dupeless_names]

    playlists_by_vocab = tfidf_vec.fit_transform(playlistnames).toarray()
    input_by_vocab = tfidf_vec.transform([song]).toarray()
    idx_to_vocab = {i:v for i, v in enumerate(tfidf_vec.get_feature_names())}

    # songlist = mysql_engine.query_selector(f"""SELECT trackname FROM songs""").fetchall()
    # songlist =  [val[0] for val in songlist]
    # songlist = [val for val in songlist if val is not None]
    # #cosine similarity
    top = []
    d1 = input_by_vocab[0]
    # print(lyric_by_vocab)
    for n in range(0,len(playlistnames)):
        d2 = playlists_by_vocab[n]
        # print(d2, np.linalg.norm(d2))
        numerator = (np.dot(d1,d2))
        denom = np.linalg.norm(d1) * np.linalg.norm(d2)
        # print(denom)
        sim = numerator/denom
        top.append((n, sim))
    top = sorted(top, key=lambda x: x[1], reverse=True)
    #search dataset
    data = []
    keys = ["user_id", "_artistname_", "_trackname_", "_playlistname_"]
    
    for m in range(0, 10):
        if (top[m][0] != None):
            query_sql = f"""SELECT * FROM songs WHERE _playlistname_ = '{playlistnames[top[m][0]]}' limit 1"""
            data.append(mysql_engine.query_selector(query_sql))
        
    result_list = []
    for cursor in data: 
        for i in cursor: 
            result_list.append(dict(zip(keys,i)))
    
    return json.dumps(result_list)

def sql_search(song):
    n_feats = 5000
    tfidf_vec = build_vectorizer(n_feats, "english")

    x = ""
    for word in song.split():
        x = x + "'%%" + word.lower() + "%%'" + " OR "
    x = x[:-4]
    #query_sql = f"""SELECT playlistname FROM songs"""
    query_sql = f"""SELECT * FROM songs WHERE LOWER( _playlistname_ ) LIKE '%%{song.lower()}%%' limit 10"""
    keys = ["user_id", "_artistname_", "_trackname_", "_playlistname_"]
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
    ret = cos_search(text)
    return ret


app.run(debug=True)

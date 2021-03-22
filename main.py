from flask import Flask, render_template, request, redirect, g
from flask.globals import current_app
from flask.helpers import url_for
from google.auth.transport import requests
from google.cloud import datastore, storage
from google.cloud.datastore import key, query
import logging
import os
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:\\Users\\kanar\\Google Drive\\Classes\\Cloud Computing\\Assignment 1\\Assignment 1-8cc17cf425c1.json"
logging.basicConfig(level=logging.DEBUG)
datastore_client = datastore.Client()
storage_client = storage.Client()
app = Flask(__name__)
current_user = None

class CurrentUser:
    def __init__(self, user):
        self.user = user

@app.route('/', methods=['POST', 'GET'])
def index():
    global current_user
    g.current_user = current_user
    if request.method == 'POST':
        entered_subject = request.form['subject']
        entered_message = request.form['messagearea']
        post_message(entered_subject, entered_message)
    posts_query = datastore_client.query(kind='post')
    posts_query.order = ['-datetime']
    # posts_query = datastore_client.query()
    posts = list(posts_query.fetch())
    # app.logger.info(posts)
    # posts = datastore_client.get_multi()
    
    return render_template('index.html', posts = posts)

@app.route('/login', methods=['POST', 'GET'])
def login():
    global current_user
    g.current_user = current_user
    login_success = True
    if request.method == 'POST':
        entered_id = request.form['userid']
        entered_pass = request.form['pass']
        if login_valid(entered_id, entered_pass):
            current_user = get_user_by_userid(entered_id)
            g.current_user = current_user
            return redirect(url_for('index'))
        else:
            login_success = False
            return render_template('login.html', login_success = login_success)
    return render_template('login.html', login_success = login_success)

@app.route('/register', methods=['POST', 'GET'])
def register():
    global current_user
    g.current_user = current_user
    if request.method == 'POST':
        kind = "user"
        id = request.form["userid"]
        user_key = datastore_client.key(kind, id)
        if get_user_by_userid(id) == None:
            newUser = datastore.Entity(key=user_key)
            username = request.form['username']
            password = request.form['pass']
            # user_image = request.form['userimage']
            newUser["user_name"] = username
            newUser["password"] = password
            # upload_userimage(user_image, username)
            datastore_client.put(newUser)
            return redirect(url_for('login'))
        else:
            return render_template('register.html', register_valid=False)
    else:
        return render_template('register.html', register_valid=True)

@app.route('/user/<string:userid>', methods=['POST', 'GET'])
def user(userid):
    global current_user
    app.logger.info(current_user)
    g.current_user = current_user
    pass_change_valid = True
    if request.method == 'POST':
        with datastore_client.transaction():
            user_key = datastore_client.key("user", userid)
            user_to_change_pass_of = datastore_client.get(user_key)
            if(user_to_change_pass_of['password'] == request.form['currpass']):
                user_to_change_pass_of["password"] = request.form['newpass']
                datastore_client.put(user_to_change_pass_of)
                pass_change_valid = True
            else:
                pass_change_valid = False
    user = get_user_by_userid(userid)
    if user == None:
        return "User does not exist"
    else:
        user_posts = get_posts_by_user(userid)
        return render_template('user.html', user = user, pass_change_valid=pass_change_valid, user_posts = user_posts)

@app.route('/logout')
def logout():
    global current_user
    current_user = None
    return redirect(url_for('index'))

def get_user_by_userid(userid):
    user_key = datastore_client.key("user", str(userid))
    gotten_user = datastore_client.get(user_key)
    return  gotten_user

def post_message(subject, message):
    with datastore_client.transaction():
        post_key = datastore_client.key("post", subject)
        post = datastore.Entity(key=post_key)
        post['user'] = current_user.key.name
        post['message'] = message
        post['datetime'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        datastore_client.put(post)
    return

def get_posts_by_user(userid):
    posts_query = datastore_client.query(kind='post')
    posts_query.add_filter('user', '=', userid)
    posts_query.order = ['-datetime']
    
    return list(posts_query.fetch())
    

def login_valid(userid, password):
    valid = False
    user = get_user_by_userid(userid)
    if user != None and userid == user.key.name and password == user['password']:
        valid = True
    return valid 
    
def upload_userimage(selected_image, image_name):
    bucket = storage_client.bucket("cc-assignment1-berke")
    blob = bucket.blob(image_name)

    blob.upload_from_filename(selected_image)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
 
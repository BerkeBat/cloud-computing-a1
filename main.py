from urllib.parse import uses_fragment
from flask import Flask, json, render_template, request, redirect
from flask.helpers import url_for
from google.auth.transport import requests
from google.cloud import datastore, storage
from google.cloud.datastore import key
import logging
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:\\Users\\kanar\\Google Drive\\Classes\\Cloud Computing\\Assignment 1\\Assignment 1-8cc17cf425c1.json"
logging.basicConfig(level=logging.DEBUG)
datastore_client = datastore.Client()
storage_client = storage.Client()
app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def index():

    return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        kind = "user"
        id = request.form["userid"]
        user_key = datastore_client.key(kind, id)
        # if get_user_by_userid(user_key) is None:
        newUser = datastore.Entity(key=user_key)
        username = request.form['username']
        password = request.form['pass']
        # user_image = request.form['userimage']
        newUser["user_name"] = username
        newUser["password"] = password
        # upload_userimage(user_image, username)
        datastore_client.put(newUser)
        # else:
            # app.logger.info("user already exists.")

        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/user/<string:userid>', methods=['POST', 'GET'])
def user(userid):
    if request.method == 'POST':
        with datastore_client.transaction():
            user_key = datastore_client.key("user", userid)
            user_to_change_pass_of = datastore_client.get(user_key)
            if(user_to_change_pass_of['password'] == request.form['currpass']):
                user_to_change_pass_of["password"] = request.form['newpass']
                datastore_client.put(user_to_change_pass_of)
    user = get_user_by_userid(userid)
    return render_template('user.html', user = user)

def get_user_by_userid(userid):
    user_key = datastore_client.key("user", userid)
    gotten_user = datastore_client.get(user_key)
    return  gotten_user
    
def upload_userimage(selected_image, image_name):
    bucket = storage_client.bucket("cc-assignment1-berke")
    blob = bucket.blob(image_name)

    blob.upload_from_filename(selected_image)

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)
 
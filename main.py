from flask import Flask, render_template
from google.auth.transport import requests
from google.cloud import datastore
import google.oauth2.id_token

datastore_client = datastore.Client()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/user/<string:username>', methods=['GET', 'POST'])
def user(username):
    # query = datastore_client.query(kind="user")
    # query.add_filter("user_name", "=", username)
    # fetched_username = query.fetch()
    return render_template('user.html')

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)
 
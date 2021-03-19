from flask import Flask, render_template
from google.cloud import datastore

datastore_client = datastore.Client()
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
  app.run(host='127.0.0.1', port=8080, debug=True)
 
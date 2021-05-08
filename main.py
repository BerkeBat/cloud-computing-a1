from flask import Flask, render_template, request, redirect, g
from flask.helpers import url_for
from google.cloud import datastore, storage
import logging, os, datetime


logging.basicConfig(level=logging.DEBUG)
datastore_client = datastore.Client()
storage_client = storage.Client()
app = Flask(__name__)
current_user = None

@app.route('/', methods=['POST', 'GET'])
def index():
    global current_user
    g.current_user = current_user
    if request.method == 'POST':
        entered_subject = request.form['subject']
        entered_message = request.form['messagearea']
        post_image = request.files['postimage']
        if request.files['postimage']:
            has_image = True
        else:
            has_image = False
        if get_post_by_subject(entered_subject) == None:
            post_message(entered_subject, entered_message, has_image)
            if has_image:
                upload_image("posts", post_image, entered_subject)
        else:
            g.post_exists = True
    posts_query = datastore_client.query(kind='post')
    posts_query.order = ['-datetime']
    posts = list(posts_query.fetch(limit=10))
    
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
        username = request.form['username']
        password = request.form['pass']
        user_key = datastore_client.key(kind, id)
        user_image = request.files['userimage']
        if get_user_by_userid(id) != None:
            return render_template('register.html', register_valid=False, already_exists = "ID")
        elif len(get_user_by_username(username)) != 0:
            return render_template('register.html', register_valid=False, already_exists = "username")
        else:
            new_user = datastore.Entity(key=user_key)
            new_user["user_name"] = username
            new_user["password"] = password
            if user_image:
                upload_image("users", user_image, id)
                new_user['hasimage'] = True
            else:
                new_user['hasimage'] = False
            datastore_client.put(new_user)
            return redirect(url_for('login'))
    else:
        return render_template('register.html', register_valid=True)

@app.route('/user/<string:userid>', methods=['POST', 'GET'])
def user(userid):
    global current_user
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
        return "<a href='/'>User does not exist. Click to return to the main forum</a>"
    else:
        user_posts = get_posts_by_user(userid)
        return render_template('user.html', user = user, pass_change_valid=pass_change_valid, user_posts = user_posts)

@app.route('/editpost/<string:oldsubject>', methods=['POST', 'GET'])
def editpost(oldsubject):
    global current_user
    g.current_user = current_user
    old_post = get_post_by_subject(oldsubject)
    if request.method == 'POST':
        new_subject = request.form['subject']
        new_message = request.form['messagearea']
        if old_post['hasimage'] == True:
            new_image = request.files['postimage']
            if not new_image:
                image_changed = False
            else:
                image_changed = True
        else:
            new_image = None
            image_changed = False
        edit_message(oldsubject, new_subject, new_message, new_image, image_changed, old_post['hasimage'])
        
    return redirect('/user/' + current_user.key.name)

@app.route('/logout')
def logout():
    global current_user
    current_user = None
    g.current_user = None

    return redirect(url_for('index'))

def get_user_by_userid(userid):
    user_key = datastore_client.key("user", str(userid))
    gotten_user = datastore_client.get(user_key)

    return  gotten_user

def get_post_by_subject(subject):
    post_key = datastore_client.key("post", str(subject))
    gotten_post = datastore_client.get(post_key)

    return  gotten_post

def get_post_image_by_subject(subject):
    bucket = storage_client.bucket("cc-assignment1-berke.appspot.com")
    gotten_image = bucket.blob("posts/" + subject + ".png")
    app.logger.info(gotten_image)

    return gotten_image
    
def get_user_by_username(username):
    username_query = datastore_client.query(kind='user')
    username_query.add_filter('user_name', '=', username)

    return list(username_query.fetch())

def post_message(subject, message, hasimage):
    global current_user
    with datastore_client.transaction():
        post_key = datastore_client.key("post", subject)
        post = datastore.Entity(key=post_key)
        post['user'] = current_user['user_name']
        post['userid'] = current_user.key.name
        post['message'] = message
        post['datetime'] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        post['hasimage'] = hasimage
        post['userhasimage'] = current_user['hasimage']
        datastore_client.put(post)

    return

def edit_message(oldsubject, newsubject, newmessage, newimage, imagechanged, hasimage):
    if hasimage:
        bucket = storage_client.bucket("cc-assignment1-berke.appspot.com")
        blob = bucket.blob("{}/{}.png".format("posts", oldsubject))
        if imagechanged:
            blob.delete()
            upload_image("posts", newimage, newsubject)
        else:
            bucket.rename_blob(blob, "posts/" + newsubject + ".png")
    old_post_key = datastore_client.key('post', oldsubject)
    datastore_client.delete(old_post_key)
    post_message(newsubject, newmessage, hasimage)
    
    return

def get_posts_by_user(userid):
    posts_query = datastore_client.query(kind='post')
    posts_query.add_filter('userid', '=', userid)
    posts_query.order = ['-datetime']
    
    return list(posts_query.fetch(limit=10))
    

def login_valid(userid, password):
    valid = False
    user = get_user_by_userid(userid)
    if user != None and userid == user.key.name and password == user['password']:
        valid = True
        
    return valid 
    
def upload_image(type, selected_image, image_name):
    bucket = storage_client.bucket("cc-assignment1-berke.appspot.com")
    blob = bucket.blob(type + "/" + image_name + ".png")
    blob.upload_from_file(selected_image)

    return

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
    # app.run(host='0.0.0.0')
 
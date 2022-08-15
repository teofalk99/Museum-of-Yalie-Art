import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename

from helpers import login_required

# Configure application
app = Flask(__name__)
UPLOAD_FOLDER = './static/photos'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}



# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



Session(app)
#set database
db = SQL("sqlite:///art.db")



@app.route("/")
def homepage():
    # if no login, show user a welcome page that links to register
    if session.get("user_id") is None:
        return render_template("feed_no_login.html")

    # if default page, show the first page of the feed
    if (request.args.get("p") == None) or (request.args.get("p") == 0):

        # get list of first 10 posts and their information, input to template
        posts = db.execute("SELECT username, image, artist, time, title, comment_count, posts.id FROM posts JOIN users ON users.id = posts.artist ORDER BY posts.id DESC LIMIT 10")

        return render_template("feed.html", posts=posts, page=0)

    else:
        # get list of 10 posts depending on what page is being viewed, input to template
        posts = db.execute("SELECT username, image, artist, time, title, comment_count, posts.id FROM posts JOIN users ON users.id = posts.artist ORDER BY posts.id DESC LIMIT 10 OFFSET ?", ((int(request.args.get("p")) * 10)))

        return render_template("feed.html", posts=posts, page=int(request.args.get("p")))



@app.route("/viewpost", methods = ["GET", "POST"])
@login_required
def viewpost():
    if request.method == "POST":

        # check that user reached the post the "right way" (by clicking on the comments button)
        if request.form["comments"] != None:
            # get the selected post's info from the database
            post = db.execute("SELECT comment_count, username, image, artist, time, title, posts.id FROM posts JOIN users ON users.id = posts.artist WHERE posts.id = ?;", request.form.get("comments"))[0]

            # get the current user's username (to determine wether you can delete the post or not)
            user = db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username']

            # return a different placeholder in the comment field if there are no comments
            if post['comment_count'] == 0:
                return render_template("viewpost.html", post=post, user=user)
            else:
                # create a list of comments and their values, insert them into the template
                comments = db.execute("SELECT comment, username, time FROM comments JOIN users ON comments.commenter = users.id WHERE post = ? ORDER BY comment_id ASC;", post['id'])

                return render_template("viewpost.html", post=post, comments=comments, user=user)

            # get time and date (idk what time zone this is though, not sure how to fix that)
            time = datetime.now()
            time_now = time.strftime("%d/%m/%Y %H:%M")

    # if someone tries to access this link with get, redirect to home page
    return redirect("/")



    return redirect("/")

@app.route("/deletepost", methods=["POST"])
@login_required
def delete_post():
    # delete all comments on the post and then delete the post
    db.execute("DELETE FROM comments WHERE post = ?", request.form['delete'])
    db.execute("DELETE FROM posts WHERE id = ?", request.form['delete'])

    return render_template("feed.html", error="Post Deleted!")


@app.route("/postcomment", methods=["POST"])
@login_required
def post_comment():

    # get time and date
    time = datetime.now()
    time_now = time.strftime("%d/%m/%Y %H:%M")

    # add comment to database and update comment count for that post
    db.execute("INSERT INTO comments (comment, commenter, post, time) VALUES (?, ?, ?, ?)", request.form.get("comment_field"), session['user_id'], request.form.get("post_id"), time_now)
    db.execute("UPDATE posts SET comment_count = comment_count + 1 WHERE id = ?", request.form.get("post_id"))
    
    # get new list of post values and list of comments, update template with new values
    post = db.execute("SELECT comment_count, username, image, artist, time, title, posts.id FROM posts JOIN users ON users.id = posts.artist WHERE posts.id = ?;", request.form.get("post_id"))[0]
    comments = db.execute("SELECT comment, username, time FROM comments JOIN users ON comments.commenter = users.id WHERE post = ? ORDER BY comment_id ASC;", request.form.get("post_id"))
    
    return render_template("viewpost.html", post=post, comments=comments)


@app.route("/viewprofile")
@login_required
def view_profile():
    
    #helper function to render a profile template
    def render_profile(username):

        user_id = db.execute("SELECT id FROM users WHERE username = ?", username)
        posts = db.execute("SELECT username, image, artist, time, title, comment_count, posts.id FROM posts JOIN users ON users.id = posts.artist WHERE artist IN (SELECT id FROM users WHERE username = ?) ORDER BY posts.id DESC", username)

        return render_template("viewprofile.html", posts=posts, username=username, user=session['user_id'])

    # if no q, render the current user's profile
    if request.args.get("q") == None:
        return render_profile(db.execute("SELECT username FROM users WHERE id = ?", session['user_id'])[0]['username'])


    # check that the username input exists
    rows = db.execute("SELECT * FROM users WHERE username = ?", request.args.get("q"))

    # if the user doesn't exist
    if len(rows) != 1:
        #return an error message
        return render_template("feed.html", error="That user doesn't exist!", page=0)

    # else return the profile of the user who was searched for
    return render_profile(db.execute("SELECT username FROM users WHERE username = ?", request.args.get("q"))[0]['username'])




@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    # helper function to return an error message
    def error(problem):
        return render_template("upload.html", error = problem)


    if request.method == "POST":

        # get image from html upload
        image = request.files['image']
        # make a secure file name
        image_name = secure_filename(image.filename)

        # check that a file was uploaded
        if image.filename == '':
            error("Please upload a file!")

        # check that a title was submitted
        if not request.form.get("title"):
            return error("please select a title!")

        # create a list of all existing titles and check that the user's title doesn't already exists
        title = request.form.get("title")
        all_titles = []
        for picture in db.execute("SELECT title FROM posts"):
            all_titles.append(picture['title'])

        if title in all_titles:
            return error("A post with that title already exists!")

        # do the same as above for file names
        all_posts = []
        for picture in db.execute("SELECT image FROM posts"):
            all_posts.append(picture['image'])
        print(all_posts)

        if image_name in all_posts:
            return error("An image with that name has already been uploaded!")

        # save the image in project directory
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        # get time and date
        time = datetime.now()
        time_now = time.strftime("%d/%m/%Y %H:%M")

        # store post metadata in database
        db.execute("INSERT INTO posts (title, image, artist, time) VALUES (?, ?, ?, ?)", title, image_name,
                session['user_id'], time_now)

        # send em to the feed!
        return redirect("/")

    if request.method == "GET":
        # render the upload page
        return render_template("upload.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    # helper function for errors
    def error(problem):
        return render_template("register.html", error=problem)


    if request.method == "POST":
        # check if any of the fields are missing
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return error("Please fill out all the fields!")

        # return apology if passwords don't match
        if request.form.get("password") != request.form.get("confirmation"):
            return error("Passwords do not match!")

        #make sure user uses a yale email
        if "@yale.edu" not in request.form.get("email"):
            return error("Please use Yale email!")

        #check if username or email is in use
        user_email_check = db.execute("SELECT COUNT(*) FROM users WHERE username = ? OR email = ?", request.form.get("username"), request.form.get("email"))[0]["COUNT(*)"]
        if user_email_check != 0:
            return error("Invalid username/email!")

        # otherwise inser the new user's info into database
        db.execute("INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)", request.form.get("username"),
                    generate_password_hash(request.form.get("password")), request.form.get("email"))

        #automatically log user in
        session["user_id"] = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))[0]["id"]


        #redirect to feed
        return redirect("/")


    if request.method == "GET":
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    # helper function for error messages
    def error(problem):
        return render_template("login.html", error=problem)

    if request.method == "POST":
        # check that username was submitted
        if not request.form.get("username"):
            return error("Please enter a username or email!")

        # check that password was submitted
        elif not request.form.get("password"):
            return apology("Please enter a password!")

        # search database for username
        rows = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", request.form.get("username"), request.form.get("username"))

        # make sure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], request.form.get("password")):
            return error("Invalid username/email/password!")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect("/")

    if request.method == "GET":
        return render_template("login.html")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    # helper function for returning error message
    def error(problem):
        return render_template("changepassword.html", error=problem)

    if request.method == "POST":
        # check that old password is correct
        if check_password_hash(db.execute("SELECT password_hash FROM users WHERE id = ?", session['user_id'])[0]['password_hash'], request.form.get("oldpass")):

            # if it is, change the user's pass to the new input
            db.execute("UPDATE users SET password_hash = ? WHERE id = ?", generate_password_hash(
                request.form.get("newpass")), session['user_id'])
        # return the same page with a banner confirming the password was changed! (not really an error but it works)
            return error("Password changed!")

        else:
            return error("Invalid old password")

    else:
        return render_template("changepassword.html")





@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")
from app import app
from flask import render_template, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import messages, users

@app.route("/")
def index():
    topiclist = messages.get_topic_list()
    return render_template("index.html", count=len(topiclist), topics=topiclist, username = users.username())

# Route functionality for new user registrations
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("/register.html", username = users.username())
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password2 = request.form["password2"]
        visibility = request.form["visibility"]
        if users.register(username, password, password2, visibility):
            return render_template("index.html", message="Registration succesful. You can now login.")
        else:
            return render_template("error.html", message="Registration failed.")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("index.html")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if users.login(username, password):
            return redirect("/")
        else:
            return render_template("error.html", message="User not found. Check username and password.")

@app.route("/logout")
def logout():
    users.logout()
    return redirect("/")

@app.route("/newtopic", methods=["POST"])
def newtopic():
    category = request.form["category"].lower()
    title = request.form["title"]
    message = request.form["message"]
    if session["csrf_token"] != request.form["csrf_token"]:
        return render_template("error.html", message="Forbidden")
    if users.get_can_post(session["user_id"]) == False:
        return render_template("error.html", message="An admin user has blocked you from posting.")
    if messages.newtopic(title, message, category):
        return redirect("/")
    else:
        return render_template("error.html", message="Failed to post new topic")

@app.route("/respond/<int:topic>", methods=["GET", "POST"])
def respond(topic):
    list = messages.get_responses(topic)
    title = messages.get_topic_title(topic)
    startmessage = messages.get_topic_message(topic)
    startuser = messages.get_topic_user(topic)
    categoryid = messages.get_topic_category(topic)
    category = messages.get_category_name(categoryid)
    adminstatus = users.get_admin_status(session["user_id"])
    if request.method == "GET":
        return render_template("topicpage.html", topic=topic, category=category, categoryid = categoryid, messages=list, title=title, startuser=startuser, startmessage=startmessage, username=users.username(), adminstatus = adminstatus)
    if request.method == "POST":
        if session["csrf_token"] != request.form["csrf_token"]:
            return render_template("error.html", message="Forbidden")
        elif users.get_can_post(session["user_id"]) == False:
            return render_template("error.html", message="An admin user has blocked you from posting.")
        else:
            content = request.form["content"]
            if messages.respond(content, topic):
                return redirect("/respond/" + str(topic))
            else:
                return render_template("error.html", message="Failed to post response")

@app.route("/help", methods=["GET"])
def help():
    return render_template("help.html")

@app.route("/hidetopic/<int:topic>", methods=["POST"])
def hidetopic(topic):
    if session["user_id"] == messages.get_topic_user(topic)[0][0]:
        messages.hide_topic(topic)
        return redirect("/")
    elif users.get_admin_status(session["user_id"]) == True:
        messages.hide_topic(topic)
        return redirect("/")
    else:
        return render_template("error.html", message="You do not have permission to delete this topic")
    
@app.route("/hidemessage/<int:messageid>", methods=["POST"])
def hidemessage(messageid):
    if session["user_id"] == messages.get_message_user(messageid)[0][0]:
        messages.hide_message(messageid)
        return redirect("/")
    elif users.get_admin_status(session["user_id"]) == True:
        messages.hide_message(messageid)
        return redirect("/")
    else:
        return render_template("error.html", message="You do not have permission to delete this message")
    
@app.route("/userpage/<int:user_id>", methods=["GET"])
def userpage(user_id):
    profilename = users.get_username(user_id)
    list = users.get_user_topics(user_id)
    adminlist = users.admin_get_user_topics(user_id)
    visibility = users.get_profile_visibility(user_id)
    adminstatus = users.get_admin_status(session["user_id"])
    useradminstatus = users.get_admin_status(user_id)
    canpost = users.get_can_post(user_id)
    if session["user_id"] == user_id:
        return render_template("userpage.html", message="This is your own profile. Only you can see posts you've deleted previously.", user_id = user_id, profilename = users.get_username(user_id), profileposts = adminlist, postamount = len(adminlist), visibility = True, adminstatus = adminstatus, useradminstatus = useradminstatus, canpost = canpost)
    else:
        return render_template("userpage.html", message="This is another user's profile.", user_id = user_id, profilename = profilename, profileposts = list, postamount = len(list), visibility = visibility, adminstatus = adminstatus, useradminstatus = useradminstatus, canpost = canpost)

@app.route("/banuser/<int:user_id>", methods=["GET"])
def banuser(user_id):
    if users.get_admin_status(session["user_id"]):
        users.admin_ban_user(user_id)
        return redirect("/")
    else:
        render_template("error.html", message="You do not have permission to block this user from posting.")

@app.route("/unbanuser/<int:user_id>", methods=["GET"])
def unbanuser(user_id):
    if users.get_admin_status(session["user_id"]):
        users.admin_unban_user(user_id)
        return redirect("/")
    else:
        render_template("error.html", message="You do not have permission to allow this user to post.")

@app.route("/category/<int:categoryid>", methods=["GET"])
def category(categoryid):
    categoryname = messages.get_category_name(categoryid)
    catlist = messages.get_category_topics(categoryid)
    return render_template("categorypage.html", categoryposts = catlist, categoryname = categoryname, postamount = len(catlist))
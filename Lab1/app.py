import re
import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_mail import Mail, Message
from flask_session import Session
import requests

app = Flask(__name__)

#api URL
book_api = "https://www.googleapis.com/books/v1/volumes"

#Configure session
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Required that "Less secure app access" be on
# https://support.google.com/accounts/answer/6010255
app.config["MAIL_DEFAULT_SENDER"] = "cafebot2000@gmail.com" #retreived as environmental variable
app.config["MAIL_PASSWORD"] = "coffee200!$" #retreived as environmental variable
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = 'smtp.gmail.com'
app.config["MAIL_USE_TLS"] = True #encription
app.config["MAIL_USERNAME"] = "cafebot2000@gmail.com"
mail = Mail(app)


db = SQL("postgres://tdordoxeldwmqu:8f5dd3c7322b6a83fa9279eb76cdc139979adcc7b3c03ace597bac1661d1e696@ec2-34-239-196-254.compute-1.amazonaws.com:5432/dal40v64r9dbnv")



@app.route('/')
def index():
    if not session.get("name") or not session.get("password"):
        return redirect("/login")
    
    return render_template("index.html", sports=SPORTS)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #then it was sent in correctly
        
        ##before asigning session variable the user credentials should be checked
        session["name"] = request.form.get("name")
        session["password"] = request.form.get("password")
        
        if does_user_exist():
            #then they are logged in
            return redirect("/")
        
    #otherwise they need to login with valid credentials
    return render_template("login.html")

def does_user_exist():
    """True is there is one user matching the login credentials"""
    user = db.execute("SELECT * FROM users \
                    WHERE name = ? AND password = ?", session["name"], session["password"])
    
    if(len(user) == 0):
        #then no user exsists for this name and password
        return False
    elif(len(user) == 1):
        #then one user exists
        session["user_id"] = user[0]["id"]
        return True
    else:
        #then multiple users exist and this is an issue
        return render_template("error.html", message="Multiple Users Under Same Credentials")
        

@app.route("/signUp", methods=["GET", "POST"])
def signUp():
    if request.method == "POST":
        #then it was sent in correctly
        
        ##before asigning session variable the user credentials should be checked
        session["name"] = request.form.get("name")
        session["password"] = request.form.get("password")
        
        if does_user_exist():
            #then they the user already exists so count them as logged in
            return redirect("/logout")
        
        sign_up_new_user()
        return redirect("/logout")
        
    #otherwise they need to login with valid credentials
    return render_template("signUp.html")

def sign_up_new_user():
    """Uses the current database to register a new user with their name and password"""
    
    db.execute("INSERT INTO users (name, password) \
                VALUES (?, ?)", session["name"], session["password"])
    
@app.route("/logout")
def logout():
    session["name"] = None
    session["password"] = None
    session["user_id"] = None
    
    return redirect('/')
    

@app.route("/search", methods=["GET", "POST"])
def search():
    books = []
    if request.method == "POST":
        #then it was sent in correctly
        
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")
        
        #search for all combos of that information
        books = db.execute("SELECT * FROM library WHERE \
                            isbn LIKE ? and \
                            title LIKE ? and \
                            author LIKE ?", f"%{isbn}%", f"%{title}%", f"%{author}%")
    
    return render_template("/search.html", books=books)

@app.route("/book", methods=["GET","POST"])
def book():
    Book = {}
    reviews = []

    if request.method == "POST":
        #then it was sent in correctly
        
        Book["isbn"] = request.form.get("isbn")
        Book["title"] = request.form.get("title")
        Book["author"] = request.form.get("author")
        Book["year"] = int(request.form.get("year"))
        
        #google api
        res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{Book['isbn']}"})
        dic = res.json()
        
        #if book is not found
        if dic["totalItems"] == 0:
            Book["averageRatings"] = "Null"
            Book["ratingsCount"] = "Null"
        else: #does not consider multiple items but oh well :-)
            Book["averageRatings"] = dic["items"][0]["volumeInfo"]["averageRating"]
            Book["ratingsCount"] = dic["items"][0]["volumeInfo"]["ratingsCount"]
        
        
        #get all previous reviews
        reviews = db.execute("SELECT * \
                            FROM reviews r  \
                            INNER JOIN users u \
                            ON r.user_id = u.id \
                            WHERE r.isbn = ?", Book["isbn"])
        
    return render_template("/book.html", book=Book, reviews=reviews)
    
@app.route("/review", methods=["GET","POST"])
def review():    

    if request.method == "POST":

        #then it was sent in correctly
        isbn = request.form.get("isbn")
        rating = int(request.form.get("rating"))
        review = request.form.get("review")      
        
        #get all previous reviews
        db.execute("INSERT INTO reviews (user_id, isbn, review, rating) \
                    VALUES (?, ?, ?, ?)", session["user_id"], isbn, review, rating) 
    return redirect('/book')
    
@app.route("/api/<isbn_10>")
def book_api(isbn_10):
    json = {
        "title": "Null",
        "author": "Null",
        "publishedDate": "Null",
        "ISBN_10": "Null",
        "ISBN_13": "Null",
        "reviewCount": "Null",
        "averageRating": "Null"
    }
    
    #basic book info
    dic = db.execute("SELECT * \
                        FROM library \
                        WHERE isbn = ?", isbn_10)
    print(dic)
    if dic is None:
        return jsonify({"error": "ISBN not found"}), 404
    
    json["title"] = dic[0]["title"]
    json["author"] = dic[0]["author"]
    json["ISBN_10"] = dic[0]["isbn"]
    
    #use api to get extra info
    #google api
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{dic[0]['isbn']}"})
    dic = res.json()
        
    #if book is not found
    if dic["totalItems"] == 0:
        json["averageRatings"] = "Null"
        json["ratingsCount"] = "Null"
    else: #does not consider multiple items but oh well :-)
        json["ISBN_13"] = dic["items"][0]["volumeInfo"]["industryIdentifiers"][1]["identifier"]
        json["reviewCount"] = dic["items"][0]["volumeInfo"]["ratingsCount"]
        json["averageRating"] = dic["items"][0]["volumeInfo"]["averageRating"]
        json["publishedDate"] = dic["items"][0]["volumeInfo"]["publishedDate"]
    
    return jsonify(json)
    
    
    
    
    
    
    
    
    
    
#####################################################################


@app.route("/deregister", methods=["POST"])
def deregister():
    #Forget registrant
    id = request.form.get("id")
    if id:
        db.execute("DELETE FROM registrants WHERE id = ?", id)
    return redirect("/registrants")
        
@app.route("/register", methods = ["POST"])
def register():
    
    #Validate name
    name = request.form.get("name")
    if not name:
        return render_template("error.html", message="Missing name")
    
    #validate sport
    sport = request.form.get("sport")
    if not sport: #did not check any boxes
        return render_template("error.html", message="Missing sport")
    if sport not in SPORTS:
        return render_template("error.html", message="Invalid sport")
    
    #validate email
    email = request.form.get("email")
    if not email: #did not check any boxes
        return render_template("error.html", message="Missing email")
    
    #Remember registrant
    db.execute("INSERT INTO registrants (name, sport, email) VALUES(?, ?, ?)", name, sport, email)
    
    #Send email
    message = Message("You are registered!", recipients=[email])
    mail.send(message)
    
    #Confirm registration
    return redirect("/registrants")

@app.route("/registrants")
def registrants():
    registrants = db.execute("SELECT * FROM registrants")
    
    return render_template("registrants.html", registrants=registrants)
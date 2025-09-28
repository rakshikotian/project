from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.utils import secure_filename
import os


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for sessions

# MySQL config (match your phpMyAdmin settings)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'   # change if you set a user
app.config['MYSQL_PASSWORD'] = ''   # enter your MySQL password if any
app.config['MYSQL_DB'] = 'ebook_shelf'

mysql = MySQL(app)

@app.route("/")
def home():
    return render_template("index.html")

# ---------------- Signup ----------------
@app.route("/signup", methods=["POST"])
def signup():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    account = cursor.fetchone()

    if account:
        flash("Account already exists with this email!", "danger")
    elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
        flash("Invalid email address!", "danger")
    else:
        cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", 
                       (username, email, password))
        mysql.connection.commit()
        flash("You have successfully registered!", "success")
    return redirect(url_for("home"))

# ---------------- Login ----------------
@app.route("/login", methods=["POST"])
def login():
    email = request.form['email']
    password = request.form['password']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    account = cursor.fetchone()

    if account:
        print("DEBUG account:", account)
        session['loggedin'] = True
        session['id'] = account['user_id']
        session['username'] = account['username']
        session['user_email'] = account['email']   
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Incorrect username/password!", "danger")
        return redirect(url_for("home"))

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        query = """
        SELECT books.book_id, books.title, books.author, books.description, books.cover_url, books.pdf_url,
               categories.categories AS genre
        FROM books
        JOIN categories ON books.category_id = categories.category_id;
        """
        cursor.execute(query)
        books = cursor.fetchall()
        cursor.close()

        user_id = session['id']
        user_cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        user_cursor.execute("SELECT username, email, bio, profile_pic_url, location FROM users WHERE user_id=%s", (user_id,))
        user = user_cursor.fetchone()
        user_cursor.close()

        # Avatar initial fallback
        initial = user['username'][0].upper() if user and user['username'] else '?'

        # Load favourites
        fav_cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        fav_cursor.execute("""
            SELECT b.book_id, b.title, b.author, b.cover_url, b.pdf_url
            FROM user_favourites f
            JOIN books b ON f.book_id = b.book_id
            WHERE f.user_id = %s
        """, (session['id'],))
        favourite_books = fav_cursor.fetchall()
        fav_cursor.close()

        return render_template(
            'dashboard.html',
            username=user['username'],
            email=user['email'],
            user_initial=initial,
            user=user,   # ✅ pass the full user object
            books=books,
            favourite_books=favourite_books
        )
    return redirect(url_for('login'))


@app.route('/my_shelf')
def my_shelf():
    if 'loggedin' not in session:
        return jsonify({
            "success": False,
            "message": "Not logged in",
            "books": []
        })

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    cursor.execute("""
        SELECT b.book_id, b.title, b.author, b.category_id, b.description,
               b.cover_url, b.pdf_url,
               ub.status, ub.progress, ub.started_at
        FROM user_bookshelf ub
        JOIN books b ON ub.book_id = b.book_id
        WHERE ub.user_id = %s
    """, (user_id,))

    books = cursor.fetchall()
    cursor.close()

    return jsonify({
        "success": True,
        "books": books
    })

@app.route('/add_to_shelf', methods=['POST'])
def add_to_shelf():
    if 'loggedin' not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.get_json()
    book_id = data.get('book_id')
    user_id = session['id']
 # 🔎 Debug print – add here
    print("DEBUG add_to_shelf user_id:", user_id, "book_id:", book_id)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Check if already in shelf
    cursor.execute(
        "SELECT * FROM user_bookshelf WHERE user_id = %s AND book_id = %s",
        (user_id, book_id)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.close()
        return jsonify({"success": False, "message": "Book already in shelf"})

    # Insert new
    cursor.execute(
        "INSERT INTO user_bookshelf (user_id, book_id, status, progress, started_at) "
        "VALUES (%s, %s, %s, %s, NOW())",
        (user_id, book_id, 'Not Started', 0)
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"success": True, "message": "Book added to shelf"})


@app.route("/update_progress", methods=["POST"])
def update_progress():
    if "loggedin" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    data = request.get_json()
    book_id = data.get("book_id")
    progress = data.get("progress", 0)
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        UPDATE user_bookshelf 
        SET progress=%s 
        WHERE user_id=%s AND book_id=%s
    """, (progress, session["id"], book_id))
    mysql.connection.commit()
    cursor.close()
    
    return jsonify({"success": True, "progress": progress})

@app.route("/get_progress", methods=["POST"])
def get_progress():
    if "loggedin" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401
    
    data = request.get_json()
    book_id = data.get("book_id")
    
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT progress FROM user_bookshelf 
        WHERE user_id = %s AND book_id = %s
    """, (session["id"], book_id))
    result = cursor.fetchone()
    cursor.close()
    
    progress = result[0] if result else 0
    
    return jsonify({"success": True, "progress": progress})

@app.route("/search_books")
def search_books():
    query = request.args.get("q", "").strip()

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, b.description, c.categories, b.cover_url, b.pdf_url 
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.title LIKE %s OR c.categories LIKE %s
    """, (f"%{query}%", f"%{query}%"))

    results = cursor.fetchall()
    cursor.close()

    books = [
        {
            "book_id": row[0],
            "title": row[1],
            "author": row[2],
            "description": row[3],
            "category": row[4],  # categories table value
            "cover_url": url_for('static', filename=row[5]) if row[5] else "",
            "pdf_url": url_for('static', filename=row[6]) if row[6] else "",
        }
        for row in results
    ]

    return jsonify({"success": True, "books": books})

@app.route("/categories")
def get_categories():
    cur = mysql.connection.cursor()
    cur.execute("SELECT category_id, categories FROM categories")
    rows = cur.fetchall()
    cur.close()
    return jsonify([{"id": row[0], "name": row[1]} for row in rows])

@app.route("/books/category/<int:category_id>")
def get_books_by_category(category_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT book_id, title, author, description, category_id, cover_url, pdf_url
        FROM books 
        WHERE category_id = %s
    """, (category_id,))
    rows = cur.fetchall()
    cur.close()

    books = [
        {
            "book_id": row[0],
            "title": row[1],
            "author": row[2],
            "description": row[3],
            "category_id": row[4],
            "cover_url": row[5],
            "pdf_url": row[6]
        }
        for row in rows
    ]
    return jsonify(books)

@app.route("/book/<int:book_id>")
def get_book(book_id):
    if "loggedin" not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, b.description, 
               c.categories, b.cover_url, b.pdf_url
        FROM books b
        JOIN categories c ON b.category_id = c.category_id
        WHERE b.book_id = %s
    """, (book_id,))
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return jsonify({"success": False, "message": "Book not found"}), 404

    book = {
        "book_id": row[0],
        "title": row[1],
        "author": row[2],
        "description": row[3],
        "": row[4],
        "cover_url": url_for("static", filename=row[5]) if row[5] else "",
        "pdf_url": url_for("static", filename=row[6]) if row[6] else "",
    }

    return jsonify({"success": True, "book": book})
@app.route('/add_favourite', methods=['POST'])
def add_favourite():
    if 'loggedin' not in session:
        return jsonify({"success": False, "message": "Not logged in"})

    data = request.get_json()
    book_id = data.get("book_id")
    user_id = session['id']

    cursor = mysql.connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO user_favourites (user_id, book_id) VALUES (%s, %s)",
            (user_id, book_id)
        )
        mysql.connection.commit()
    except:
        # duplicate favourite
        mysql.connection.rollback()
        cursor.close()
        return jsonify({"success": False, "message": "Already in favourites"})
    
    cursor.close()
    return jsonify({"success": True, "message": "Added to favourites"})
@app.route('/remove_favourite', methods=['POST'])
def remove_favourite():
    if 'loggedin' not in session:
        return jsonify({"success": False})

    data = request.get_json()
    book_id = data.get("book_id")
    user_id = session['id']

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM user_favourites WHERE user_id=%s AND book_id=%s", (user_id, book_id))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"success": True})
@app.route('/get_favourites')
def get_favourites():
    if 'loggedin' not in session:
        return jsonify({"success": False, "books": []})

    user_id = session['id']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("""
        SELECT b.book_id, b.title, b.author, b.cover_url, b.pdf_url
        FROM user_favourites f
        JOIN books b ON f.book_id = b.book_id
        WHERE f.user_id = %s
    """, (user_id,))
    books = cursor.fetchall()
    cursor.close()

    return jsonify({"success": True, "books": books})

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "loggedin" not in session:
        return redirect(url_for("login"))

    user_id = session["id"]
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    if request.method == "POST":
        bio = request.form.get("bio")
        location = request.form.get("location")
        profile_pic = request.files.get("profile_pic")

        # Update bio & location
        cursor.execute(
            "UPDATE users SET bio=%s, location=%s WHERE user_id=%s",
            (bio, location, user_id)
        )

        # If profile picture uploaded
        if profile_pic and profile_pic.filename:
            filename = secure_filename(profile_pic.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            profile_pic.save(filepath)
            cursor.execute(
                "UPDATE users SET profile_pic_url=%s WHERE user_id=%s",
                (filename, user_id)
            )

        mysql.connection.commit()
        cursor.close()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("dashboard"))

    # On GET, fetch current user info
    cursor.execute(
        "SELECT username, email, bio, profile_pic_url, location FROM users WHERE user_id=%s",
        (user_id,)
    )
    user = cursor.fetchone()
    cursor.close()

    return render_template("edit_profile.html", user=user)

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.clear()  # clear all user session data
    return redirect(url_for("home"))  # send back to home page


print("Server is running!")
if __name__ == "__main__":  
    app.run(debug=True)
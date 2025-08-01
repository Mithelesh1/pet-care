from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner TEXT,
        name TEXT,
        age INTEGER,
        pet_type TEXT,
        image TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        service TEXT,
        date TEXT,
        time TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        message TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT,
        email TEXT,
        address TEXT,
        contact TEXT,
        city TEXT,
        state TEXT,
        country TEXT,
        pet_name TEXT,
        pet_type TEXT,
        pet_breed TEXT,
        pet_color TEXT,
        image TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# ---------- Main Pages ----------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        message = request.form['message']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO contacts (name, email, phone, message) VALUES (?, ?, ?, ?)",
                  (name, email, phone, message))
        conn.commit()
        conn.close()

        flash("Thanks for contacting us!")
        return redirect('/contact')

    return render_template('contact.html')

@app.route('/donate', methods=['GET', 'POST'])
def donate():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        address = request.form['address']
        contact = request.form['contact']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        pet_name = request.form['pet_name']
        pet_type = request.form['pet_type']
        pet_breed = request.form['pet_breed']
        pet_color = request.form['pet_color']
        image = request.files['image']

        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO donations (full_name, email, address, contact, city, state, country, pet_name, pet_type, pet_breed, pet_color, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (full_name, email, address, contact, city, state, country, pet_name, pet_type, pet_breed, pet_color, filename))
        conn.commit()
        conn.close()

        flash('Donation submitted successfully!')
        return redirect('/donate')

    return render_template('donate.html')

# ---------- Auth ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash('All fields are required!')
            return redirect('/register')

        password_hash = generate_password_hash(password)

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            flash('Registration successful! Please log in.')
            return redirect('/login')
        except:
            flash('Username already exists!')
            return redirect('/register')
        finally:
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            session['username'] = username
            flash('Login successful!')
            return redirect('/dashboard')
        else:
            flash('Invalid username or password!')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')
    return render_template('dashboard.html', username=session['username'])

# ---------- Pet Management ----------
@app.route('/add-pet', methods=['GET', 'POST'])
def add_pet():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        pet_type = request.form['pet_type']
        image = request.files['image']

        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO pets (owner, name, age, pet_type, image) VALUES (?, ?, ?, ?, ?)",
                  (session['username'], name, age, pet_type, filename))
        conn.commit()
        conn.close()

        flash('Pet added successfully!')
        return redirect('/pets')

    return render_template('add_pet.html')

@app.route('/pets')
def pets():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT name, pet_type, age, image FROM pets WHERE owner = ?", (session['username'],))
    pets_data = c.fetchall()
    conn.close()

    pets = [{'name': pet[0], 'pet_type': pet[1], 'age': pet[2], 'image': pet[3]} for pet in pets_data]

    return render_template('pets.html', pets=pets)

# ---------- Booking ----------
@app.route('/book', methods=['GET', 'POST'])
def book_service():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        service = request.form['service']
        date = request.form['date']
        time = request.form['time']

        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("INSERT INTO bookings (user, service, date, time) VALUES (?, ?, ?, ?)",
                  (session['username'], service, date, time))
        conn.commit()
        conn.close()
        flash('Service booked successfully!')
        return redirect('/my-bookings')

    return render_template('book_service.html')

@app.route('/my_booking', methods=['POST'])
def my_booking():
    if 'username' not in session:
        return redirect('/login')

    name = request.form['name']
    email = request.form['email']
    date = request.form['date']
    time = request.form['time']
    service = request.form['service']

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT INTO bookings (user, service, date, time) VALUES (?, ?, ?, ?)",
              (session['username'], service, date, time))
    conn.commit()
    conn.close()

    flash('Booking successful!')
    return redirect('/my-bookings')

@app.route('/my-bookings')
def my_bookings():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE user = ?", (session['username'],))
    bookings = c.fetchall()
    conn.close()
    return render_template('my_bookings.html', bookings=bookings)

# ---------- Privacy & Terms ----------
@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

# ---------- Run ----------
if __name__ == '__main__':
    app.run(debug=True)

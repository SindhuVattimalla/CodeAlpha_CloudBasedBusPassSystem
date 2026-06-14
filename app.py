from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import random
import string

app = Flask(__name__)
app.secret_key = "buspasssecretkey"

# Database Initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buses(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        route TEXT,
        price INTEGER
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        route TEXT,
        travel_date TEXT,
        tickets INTEGER,
        total_price INTEGER,
        pass_id TEXT UNIQUE
    )
    ''')

    # Insert bus routes only once
    cursor.execute("SELECT COUNT(*) FROM buses")
    count = cursor.fetchone()[0]

    if count == 0:
        buses = [
            ('Hyderabad → Warangal', 150),
            ('Hyderabad → Karimnagar', 180),
            ('Hyderabad → Nizamabad', 220),
            ('Hyderabad → Adilabad', 300)
        ]

        cursor.executemany(
            "INSERT INTO buses(route, price) VALUES (?, ?)",
            buses
        )

    conn.commit()
    conn.close()


init_db()


# Home Page
@app.route('/')
def home():
    return redirect(url_for('login'))


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    message = ""

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(name,email,password) VALUES(?,?,?)",
                (name, email, password)
            )

            conn.commit()
            message = "Registration Successful!"

        except:
            message = "Email already exists!"

        conn.close()

    return render_template('register.html', message=message)


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session['email'] = email
            return redirect(url_for('dashboard'))
        else:
            message = "Invalid Credentials"

    return render_template('login.html', message=message)


# Dashboard
@app.route('/dashboard')
def dashboard():

    if 'email' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM buses")
    buses = cursor.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        buses=buses
    )


# Booking
@app.route('/booking/<int:bus_id>', methods=['GET', 'POST'])
def booking(bus_id):

    if 'email' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM buses WHERE id=?",
        (bus_id,)
    )

    bus = cursor.fetchone()

    if request.method == 'POST':

        date = request.form['travel_date']
        tickets = int(request.form['tickets'])

        route = bus[1]
        price = bus[2]

        # Prevent incorrect pricing
        total = price * tickets

        # Unique Pass ID
        pass_id = "BP" + ''.join(
            random.choices(
                string.digits,
                k=6
            )
        )

        cursor.execute('''
        INSERT INTO bookings(
            user_email,
            route,
            travel_date,
            tickets,
            total_price,
            pass_id
        )
        VALUES(?,?,?,?,?,?)
        ''', (
            session['email'],
            route,
            date,
            tickets,
            total,
            pass_id
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                'ticket',
                pass_id=pass_id
            )
        )

    conn.close()

    return render_template(
        'booking.html',
        bus=bus
    )


# Ticket
@app.route('/ticket/<pass_id>')
def ticket(pass_id):

    if 'email' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute(
        '''
        SELECT * FROM bookings
        WHERE pass_id=?
        ''',
        (pass_id,)
    )

    booking = cursor.fetchone()

    conn.close()

    return render_template(
        'ticket.html',
        booking=booking
    )


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
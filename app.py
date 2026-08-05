from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'starvehiclepro_secret_key_2024'

DATABASE = 'star_vehicle.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Vehicles table
    c.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price REAL NOT NULL,
            condition TEXT NOT NULL,
            fuel_type TEXT NOT NULL,
            transmission TEXT NOT NULL,
            mileage INTEGER,
            description TEXT,
            location TEXT,
            image_url TEXT DEFAULT '/static/images/default-car.jpg',
            status TEXT DEFAULT 'available',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Check if admin exists, if not create default admin
    c.execute("SELECT * FROM users WHERE email = ?", ('admin@starvehicle.pro',))
    if not c.fetchone():
        admin_hash = generate_password_hash('admin123')
        c.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, ('Administrator', 'admin@starvehicle.pro', '0000000000', admin_hash, 'admin'))

    conn.commit()
    conn.close()

@app.route('/')
def home():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT v.*, u.full_name as seller_name FROM vehicles v JOIN users u ON v.user_id = u.id WHERE v.status = 'available' ORDER BY v.created_at DESC LIMIT 6")
    vehicles = c.fetchall()
    conn.close()
    return render_template('home.html', vehicles=vehicles)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return redirect(url_for('register'))

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            flash('Email already registered!', 'error')
            conn.close()
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        c.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, (full_name, email, phone, password_hash, 'user'))

        conn.commit()
        conn.close()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_role'] = user['role']
            flash(f'Welcome back, {user["full_name"]}!', 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'user':
        flash('Please login as a user.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    c.execute("SELECT * FROM vehicles WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],))
    my_vehicles = c.fetchall()
    conn.close()

    return render_template('user_dashboard.html', user=user, vehicles=my_vehicles)

@app.route('/user/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']

        c.execute("""
            UPDATE users SET full_name = ?, email = ?, phone = ? WHERE id = ?
        """, (full_name, email, phone, session['user_id']))

        conn.commit()
        conn.close()

        session['user_name'] = full_name
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    c.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    conn.close()

    return render_template('edit_profile.html', user=user)

@app.route('/user/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'user_id' not in session or session.get('user_role') != 'user':
        flash('Please login as a user.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        brand = request.form['brand']
        model = request.form['model']
        year = request.form['year']
        price = request.form['price']
        condition = request.form['condition']
        fuel_type = request.form['fuel_type']
        transmission = request.form['transmission']
        mileage = request.form.get('mileage', 0)
        description = request.form['description']
        location = request.form['location']

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO vehicles (user_id, title, brand, model, year, price, condition, fuel_type, transmission, mileage, description, location)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session['user_id'], title, brand, model, year, price, condition, fuel_type, transmission, mileage, description, location))

        conn.commit()
        conn.close()

        flash('Vehicle listed successfully!', 'success')
        return redirect(url_for('user_dashboard'))

    return render_template('add_vehicle.html')

@app.route('/user/delete_vehicle/<int:vehicle_id>')
def delete_vehicle(vehicle_id):
    if 'user_id' not in session:
        flash('Please login first.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE id = ? AND user_id = ?", (vehicle_id, session['user_id']))
    conn.commit()
    conn.close()

    flash('Vehicle deleted successfully!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Access denied! Admin only.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM users")
    total_users = c.fetchone()['total']
    c.execute("SELECT COUNT(*) as total FROM vehicles")
    total_vehicles = c.fetchone()['total']
    c.execute("SELECT * FROM users WHERE role = 'user' ORDER BY created_at DESC")
    users = c.fetchall()
    c.execute("SELECT v.*, u.full_name as seller_name FROM vehicles v JOIN users u ON v.user_id = u.id ORDER BY v.created_at DESC")
    vehicles = c.fetchall()
    conn.close()

    return render_template('admin_dashboard.html', total_users=total_users, total_vehicles=total_vehicles, users=users, vehicles=vehicles)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
def admin_edit_user(user_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()

    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        role = request.form['role']

        c.execute("""
            UPDATE users SET full_name = ?, email = ?, phone = ?, role = ? WHERE id = ?
        """, (full_name, email, phone, role, user_id))

        conn.commit()
        conn.close()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()

    return render_template('admin_edit_user.html', user=user)

@app.route('/admin/delete_user/<int:user_id>')
def admin_delete_user(user_id):
    if 'user_id' not in session or session.get('user_role') != 'admin':
        flash('Access denied!', 'error')
        return redirect(url_for('login'))

    if user_id == session['user_id']:
        flash('You cannot delete yourself!', 'error')
        return redirect(url_for('admin_dashboard'))

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM vehicles WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/vehicles')
def all_vehicles():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT v.*, u.full_name as seller_name FROM vehicles v JOIN users u ON v.user_id = u.id WHERE v.status = 'available' ORDER BY v.created_at DESC")
    vehicles = c.fetchall()
    conn.close()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/vehicle/<int:vehicle_id>')
def vehicle_detail(vehicle_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT v.*, u.full_name as seller_name, u.email as seller_email, u.phone as seller_phone FROM vehicles v JOIN users u ON v.user_id = u.id WHERE v.id = ?", (vehicle_id,))
    vehicle = c.fetchone()
    conn.close()

    if not vehicle:
        flash('Vehicle not found!', 'error')
        return redirect(url_for('all_vehicles'))

    return render_template('vehicle_detail.html', vehicle=vehicle)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

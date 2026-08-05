# Star Vehicle PRO

A complete vehicle exchange platform built with Python Flask.

## Features

- User Registration & Login
- Password Encryption (Werkzeug hashing)
- Two User Roles: Admin & User
- SQLite Database
- Dynamic Website
- Responsive Design (works on phone & desktop)
- Admin can: View Users, Edit Users, Delete Users
- User can: Register, Login, Edit Profile, Add/List/Delete Vehicles

## Quick Start (Local)

1. Install Python 3.8+ from https://python.org

2. Open terminal/command prompt in this folder

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Run the app:
```
python app.py
```

5. Open browser: http://127.0.0.1:5000

## Default Admin Login
- Email: admin@starvehicle.pro
- Password: admin123

## Free Deploy on Render

1. Go to https://render.com and sign up (free)
2. Click "New +" → "Web Service"
3. Connect your GitHub repo OR upload this folder
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Python Version: 3.11
5. Click "Deploy"
6. Your site goes live with a free URL!

## Free Deploy on PythonAnywhere

1. Go to https://pythonanywhere.com and sign up (free)
2. Upload this folder
3. Create a new web app with Flask
4. Point it to app.py
5. Done!

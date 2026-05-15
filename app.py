from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

# FIREBASE SETUP

if os.path.exists("firebase_key.json"):

    cred = credentials.Certificate(
        "firebase_key.json"
    )

# RENDER DEPLOYMENT

else:

    firebase_config = json.loads(
        os.environ.get("FIREBASE_KEY")
    )

    cred = credentials.Certificate(
        firebase_config
    )

firebase_admin.initialize_app(cred)

db = firestore.client()

# FLASK APP

app = Flask(__name__)
app.secret_key = "secret123"

# ADMIN CREDENTIALS

ADMIN_USERNAME = "Parshan"
ADMIN_PASSWORD = "18_may26"

# HOME PAGE

@app.route('/')
def home():
    return render_template('home.html')

# REGISTER PAGE

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        users_ref = db.collection('users')

        existing_users = users_ref.where(
            'username', '==', username
        ).stream()

        for user in existing_users:
            flash("Username already exists")
            return redirect('/register')

        hashed_password = generate_password_hash(password)

        users_ref.add({
            'username': username,
            'password': hashed_password
        })

        flash("Registration Successful")

        return redirect('/login')

    return render_template('register.html')

# LOGIN PAGE

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')

        # ADMIN LOGIN

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session.clear()

            session['admin'] = True

            return redirect('/admin/dashboard')

        # USER LOGIN

        users_ref = db.collection('users')

        users = users_ref.where(
            'username', '==', username
        ).stream()

        for user in users:

            user_data = user.to_dict()

            if check_password_hash(
                user_data['password'],
                password
            ):

                session.clear()

                session['username'] = username

                return redirect('/dashboard')

        flash("Wrong Username or Password")

    return render_template('login.html')

# USER DASHBOARD

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    if 'username' not in session:
        return redirect('/login')

    username = session['username']

    # ADD NOTE

    if request.method == 'POST':

        title = request.form.get('title')
        content = request.form.get('content')

        db.collection('notes').add({
            'username': username,
            'title': title,
            'content': content
        })

        return redirect('/dashboard')

    # SEARCH

    search = request.args.get('search')

    notes_ref = db.collection('notes').where(
        'username', '==', username
    ).stream()

    notes = []

    for note in notes_ref:

        note_data = note.to_dict()

        note_data['id'] = note.id

        if search:

            if (
                search.lower() in note_data['title'].lower()
                or
                search.lower() in note_data['content'].lower()
            ):

                notes.append(note_data)

        else:

            notes.append(note_data)

    return render_template(
        'dashboard.html',
        notes=notes,
        username=username
    )

# EDIT NOTE

@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_note(id):

    note_ref = db.collection('notes').document(id)

    note = note_ref.get()

    note_data = note.to_dict()

    if request.method == 'POST':

        title = request.form.get('title')
        content = request.form.get('content')

        note_ref.update({
            'title': title,
            'content': content
        })

        return redirect('/dashboard')

    return render_template(
        'edit_note.html',
        note=note_data
    )

# DELETE NOTE

@app.route('/delete/<id>')
def delete_note(id):

    db.collection('notes').document(id).delete()

    return redirect('/dashboard')

# LOGOUT

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')

# ADMIN DASHBOARD

@app.route('/admin/dashboard')
def admin_dashboard():

    if 'admin' not in session:
        return redirect('/login')

    users = []
    notes = []

    # FETCH USERS

    users_ref = db.collection('users').stream()

    for user in users_ref:

        users.append(user.to_dict())

    # FETCH NOTES

    notes_ref = db.collection('notes').stream()

    for note in notes_ref:

        notes.append(note.to_dict())

    return render_template(
        'admin_dashboard.html',
        users=users,
        notes=notes
    )

# RUN APP

if __name__ == '__main__':
    app.run(debug=True)
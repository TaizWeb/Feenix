import sqlite3
from Crypto.Hash import SHA256
from flask import Flask
from flask import render_template
from flask import request
app = Flask(__name__)

def string_escape(string):
	return string.replace("\"", "\"\"").replace("\'", "\'\'")

@app.route('/')
def hello():
	return render_template('index.html')

@app.route('/signup', methods=['GET'])
def signup():
	return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_action():
	username_available = True
	email_available = True
	username_valid = True
	email_valid = True
	password_valid = True
	conn = sqlite3.connect('Feenix.db')
	cursor = conn.cursor()
	username = string_escape(request.form['username'])
	email = string_escape(request.form['email'])
	password = string_escape(request.form['password'])

	# Checking length requirements
	if len(request.form['username']) < 3 or len(request.form['username']) > 15:
		username_valid = False

	if len(request.form['email']) < 3 or len(request.form['email']) > 255:
		email_valid = False

	if len(request.form['password']) < 3 or len(request.form['password']) > 35:
		password_valid = False

	# Checking if the username is available
	query_string = "SELECT * FROM Users WHERE username=?;"
	cursor.execute(query_string, (username,))
	for row in cursor:
		print(row)
		username_available = False

	# Checking if the email is available
	query_string = "SELECT * FROM Users WHERE email=?;"
	cursor.execute(query_string, (email,))
	for row in cursor:
		email_available = False

	# Checking if all flags have been activated
	if username_available and email_available and username_valid and email_valid and password_valid:
		hasher = SHA256.new()
		hasher.update(str.encode(password))
		hashed_password = hasher.hexdigest()
		query_string = "INSERT INTO Users(username, password, email) VALUES('{username}', '{password}', '{email}')".format(username = username, password = hashed_password, email = email)
		cursor.execute(query_string)
		conn.commit()
		conn.close()
		return render_template('index.html')

	else:
		# add flags in clientside later
		print(username_available, email_available, username_valid, password_valid, email_valid)
		return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def signin_action():
	if request.method == 'POST':
		query_string = "SELECT * FROM Users WHERE username='{username}'".format(username = request.form['username'])
		conn = sqlite3.connect('Feenix.db')
		cursor = conn.cursor()
		cursor.execute(query_string)
		conn.commit()
		for row in cursor:
			print(row[0])
			print(row[1])
		conn.close()

		return render_template('index.html')
	else:
		return render_template('login.html')


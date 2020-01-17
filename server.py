import os
import sqlite3
import asyncio
import websockets
from Crypto.Hash import SHA256
from flask import Flask, render_template, request, make_response, session, redirect, url_for

app = Flask(__name__)
app.secret_key = os.environ['flask_secret_key']

# Returns an escaped sql string
def string_escape(string):
	return string.replace("\"", "\"\"").replace("\'", "\'\'")

# TODO: Test websocket server running along side web server capabilites, probably google a tutorial to fix the hanging issues currently plauging us
async def testsock(websocket, path):
	test = await websocket.recv()
	print(test)

# loop = asyncio.new_event_loop()
# asyncio.set_event_loop(loop)
start_server = websockets.serve(testsock, '127.0.0.1', 8767)
loop.run_until_complete(start_server)
loop.run_forever()

@app.route('/')
def index():
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
		# TODO update this to the new format
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
		# Flags
		username_exists = False
		passwords_match = False

		# Supplied form data
		username = string_escape(request.form['username'])
		password = string_escape(request.form['password'])

		# Hashing the password
		hasher = SHA256.new()
		hasher.update(str.encode(password))
		hashed_password = hasher.hexdigest()

		# Retrieving data from the database
		query_string = "SELECT * FROM Users WHERE username=?;"
		conn = sqlite3.connect('Feenix.db')
		cursor = conn.cursor()
		cursor.execute(query_string, (username,))
		conn.commit()
		for row in cursor:
			username_exists = True
			if row[2] == hashed_password:
				passwords_match = True
		conn.close()

		if username_exists and passwords_match:
			resp = make_response(render_template('home.html'))
			resp.set_cookie('login-token', username + "+" + hashed_password)
			return resp

		else:
			return render_template('login.html')

	else:
		# Checking for cookie data
		cookie_valid = False
		login_token = request.cookies.get('login-token')

		if login_token is not None:
			token_username = login_token.split("+")[0]
			token_password = login_token.split("+")[1]
			query_string = "SELECT * FROM Users WHERE password=?;"
			conn = sqlite3.connect('Feenix.db')
			cursor = conn.cursor()
			cursor.execute(query_string, (token_password,))
			conn.commit()
			for row in cursor:
				cookie_valid = True
			conn.close()

		if cookie_valid:
			# Creating a session for the user
			session['username'] = token_username
			return redirect(url_for('home'))
		else:
			return render_template('login.html')

@app.route('/logout')
def logout():
	if request.cookies.get('login-token') == '':
		return redirect(url_for('index'))

	# Destroy the session and clear the cookies to sign out the user
	session.clear()
	resp = make_response(render_template('logout.html'))
	# Setting the cookie to expire in the past
	resp.set_cookie('login-token', '', expires=0)
	return resp

@app.route('/home')
def home():
	# Checking to see if the user has an active session
	if 'username' in session:
		return render_template('home.html', username=session['username'])
	else:
		# TODO: Add a "please login" message
		return redirect(url_for('login'))

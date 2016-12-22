import os, sys, datetime, flask
from flask import Flask, flash, render_template, request, make_response, redirect, url_for, current_app, session
from werkzeug import secure_filename
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt

ALLOWED_IMG_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# check whether img extension is allowed
def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_IMG_EXTENSIONS

# look up complete garment details and return as dict
def lookUpGarment(garment):
	cursor = mysql.connection.cursor()

	cursor.execute('''SELECT tag_name FROM tag WHERE feature_type = 'garment type' AND tag_id = %s''', [garment[4]])
	garment_type = cursor.fetchone()[0]

	cursor.execute('''SELECT tag_name FROM tag WHERE feature_type = 'color' AND tag_id = %s''', [garment[5]])
	color = cursor.fetchone()[0]

	cursor.execute('''SELECT tag_name FROM tag WHERE feature_type = 'size' AND tag_id = %s''', [garment[6]])
	size = cursor.fetchone()[0]

	garmentdict = {
	'garment_id': garment[0],
	'desc': garment[1],
	'photo_loc': garment[2],
	'person_id': garment[3],
	'garment_type': garment_type,
	'color': color,
	'size': size
	}
	return garmentdict


# adds new user into person table, stores hashed password
def addUser(username, password):
    # add user
    hashedpass = bcrypt.generate_password_hash(password)
    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO person (name, password) VALUES (%s, %s)''', [username, hashedpass])
    mysql.connection.commit()

    # get person id and set session credentials
    cursor.execute('''SELECT person_id FROM person WHERE name = %s AND password = %s''', [username, hashedpass])
    person_id = cursor.fetchone()
    session['username'] = username
    session['person_id'] = person_id


# if valid login, returns person id, otherwise None
def validateLogin(username, password):
    cursor = mysql.connection.cursor()
    cursor.execute('''SELECT * FROM person WHERE name = %s''', [username,])
    person_lookup = cursor.fetchone()
    if person_lookup:
        hashedpass = person_lookup[2]
        if bcrypt.check_password_hash(hashedpass, password):
            return person_lookup[0]
    return None


@app.route('/', methods=["GET", "POST"])
def index():
	if 'username' in session:
		return redirect(url_for('browse'))
	else:
		return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
	return render_template('login.html')


# validating login credentials
@app.route('/validate', methods=['POST', 'GET'])
def validate():
	if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']

		# check login validity
		person_id = validateLogin(name, password)
        if person_id:
            response = make_response(browse())
            session['username'] = name
            session['person_id'] = person_id
        else:
            flash('Incorrect login credentials.')
            return redirect(url_for('login'))
        return response


@app.route('/register', methods=['POST', 'GET'])
def register():
    return render_template('register.html')


@app.route('/process_registration', methods=['POST', 'GET'])
def process_registration():
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
		name = request.form['name']
		password = request.form['password']
		password_confirm = request.form['password_confirm']

		if (password != password_confirm):
		    flash('Passwords did not match.')
		    return redirect(url_for('register'))
		else:
		    cursor.execute('''SELECT * FROM person WHERE name = %s''', [name,])
		    person_lookup = cursor.fetchone()
		    if person_lookup:
		        flash('Username ' + name + ' already exists. Please choose another one.')
		        return redirect(url_for('register'))
		    else:
		        addUser(name, password)
		        flash('Welcome ' + name + '!')
		        return redirect(url_for('browse'))


@app.route('/browse')
def browse():
	cursor = mysql.connection.cursor()
	cursor.execute('''SELECT * FROM garment''')
	garments_list = cursor.fetchall()
	garments = []
	for garment in garments_list:
		garments.append(lookUpGarment(garment))
	return render_template('browse.html', garments = garments)


@app.route('/error_login')
def error_login():
	return render_template('error_login.html')


@app.route('/upload')
def upload():
	return render_template('upload.html')


@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
	cursor = mysql.connection.cursor()
	if request.method == 'POST':
	        if 'username' in session:
			file = request.files['file']
			if file and allowed_file(file.filename):
				# save file to folder
				filename = secure_filename(file.filename)
				file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


				# get tag id for garment type
				cursor.execute('''SELECT tag_id FROM tag WHERE feature_type = 'garment type' AND tag_name = %s''', [request.form['garmenttype']])
				tagid_garmenttype = cursor.fetchone()[0]

				# get tag id for color
				cursor.execute('''SELECT tag_id FROM tag WHERE feature_type = 'color' AND tag_name = %s''', [request.form['color']])
				tagid_color = cursor.fetchone()[0]

				# get tag id for size
				cursor.execute('''SELECT tag_id FROM tag WHERE feature_type = 'size' AND tag_name = %s''', [request.form['size']])
				tagid_size = cursor.fetchone()[0]

				params = [request.form['description'], filename, session['person_id'], tagid_garmenttype, tagid_color, tagid_size]

				cursor.execute("""INSERT INTO garment (description, photo_loc, person_id, tag_garmenttype_id, tag_color_id, tag_size_id) VALUES (%s, %s, %s, %s, %s, %s)""", (params))
				mysql.connection.commit()

				flash('file uploaded successfully')
				return redirect(url_for('browse'))
			else:
				flash('file type not allowed')
				return redirect(url_for('browse'))
		else:
			return redirect(url_for('error_login'))
	return


@app.route('/reserve/<int:garment_id>', methods = ['GET', 'POST'])
def reserve(garment_id):
	if 'username' in session:
		cursor = mysql.connection.cursor()
		cursor.execute('''SELECT * FROM garment WHERE garment_id = %s''', [garment_id])
		garment = cursor.fetchone()
		print garment
		garment = lookUpGarment(garment)

		return render_template('reserve.html', garment=garment)
	else:
		return redirect(url_for('error_login'))


@app.route('/reserver/<int:garment_id>', methods = ['GET', 'POST'])
def reserver(garment_id):
	cursor = mysql.connection.cursor()
	if request.method == 'POST':
	        if 'username' in session:
				# record reservation into db
				# get person id

				new_start = request.form['date_start']
				new_end = request.form['date_end']


				# check whether start date for this reservation is before
				# any existing reservation end dates
				cursor.execute('''SELECT * FROM reservation WHERE garment_id = %s AND ( (date_start >= %s AND date_start <= %s) OR (date_start <= %s AND date_end >= %s))''',
				[garment_id, new_start, new_end, new_start, new_end])
				conflicts = cursor.fetchall()
				print conflicts

				if not conflicts:
					params = [request.form['date_start'], request.form['date_end'], session['person_id'], garment_id]
					print params

					cursor.execute("""INSERT INTO reservation (date_start, date_end, person_id, garment_id) VALUES (%s, %s, %s, %s)""", (params))
					mysql.connection.commit()

					flash('reservation successful!')
					return redirect(url_for('browse'))
				else:
					flash('this garment is already reserved for those dates')
					return redirect(url_for('reserve', garment_id=garment_id))
		else:
			return redirect(url_for('error_login'))
	return

@app.route('/mygarments')
def mygarments():
	cursor = mysql.connection.cursor()
	cursor.execute('''SELECT * FROM garment WHERE person_id = %s''', [session['person_id']])
	garments_list = cursor.fetchall()
	garments = []
	for garment in garments_list:
		garments.append(lookUpGarment(garment))
	return render_template('browse.html', garments = garments)

@app.route('/myreservations')
def myreservations():
	cursor = mysql.connection.cursor()
	cursor.execute('''SELECT * FROM garment WHERE garment_id IN (SELECT garment_id FROM reservation WHERE person_id = %s)''', [session['person_id']])
	garments_list = cursor.fetchall()
	garments = []
	for garment in garments_list:
		garments.append(lookUpGarment(garment))
	return render_template('browse.html', garments = garments)

app.secret_key = 'A0ZolP!j/3yX RGG8$$xmN]LWX/,?RT'


if __name__ == '__main__':
	app.run(debug = True)

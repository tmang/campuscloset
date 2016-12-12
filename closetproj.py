import os, sys, datetime, flask
from flask import Flask, render_template, request, make_response, redirect, url_for, current_app, session
from werkzeug import secure_filename
from flask_mysqldb import MySQL

ALLOWED_IMG_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL(app)

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


@app.route('/', methods=["GET", "POST"])
def index():
	if 'username' in session:
		return browse()
	else:
		return login()

@app.route('/login', methods=['POST', 'GET'])
def login():
	return render_template('login.html')

@app.route('/validate', methods=['POST', 'GET'])
def validate():
	cursor = mysql.connection.cursor()
	if request.method == 'POST':
		name = request.form['name']

		# check username validity
		cursor.execute('''SELECT * FROM person WHERE name = %s''', [name])
                person_lookup = cursor.fetchone()
                if person_lookup: 
                    if person_lookup[2] == request.form['password']:
			    response = make_response(browse())
                            session['username'] = name;
                            session['person_id'] = person_lookup[1]
                    else:
                        return 'incorrect login credentials'
		else:
			response = make_response(error_login())
		return response

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

				print 'file uploaded successfully'
				return browse()
			else:
				return 'file type not allowed'
		else:
			return error_login()
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
		return error_login()


@app.route('/reserver/<int:garment_id>', methods = ['GET', 'POST'])
def reserver(garment_id):
	cursor = mysql.connection.cursor()
	if request.method == 'POST':
	        if 'username' in session:
				# record reservation into db
				# get person id

				# check whether start date for this reservation is before
				# any existing reservation end dates
				cursor.execute('''SELECT * FROM reservation WHERE garment_id = %s AND (date_start <= %s AND ) AND)''', [garment_id, request.form['date_start']])
				conflicts = cursor.fetchall()
				print conflicts

				if not conflicts:
					params = [request.form['date_start'], request.form['date_end'], session['person_id'], garment_id]

					cursor.execute("""INSERT INTO reservation (date_start, date_end, person_id, garment_id) VALUES (%s, %s, %s, %s)""", (params))
					mysql.connection.commit()

					print 'reservation successful!'
					return browse()
				else:
					return 'this garment is already reserved for these dates'
		else:
			return error_login()
	return

app.secret_key = 'A0ZolP!j/3yX RGG8$$xmN]LWX/,?RT'


if __name__ == '__main__':
	app.run(debug = True)

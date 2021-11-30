from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Configurar MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# iniciar MYSQL
mysql = MySQL(app)

#Articles = Articles()

# Inicio
@app.route('/')
def index():
    return render_template('home.html')


# Acerca de
@app.route('/about')
def about():
    return render_template('about.html')


# entradas
@app.route('/articles')
def articles():
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entradas
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'Aún no hay entradas'
        return render_template('articles.html', msg=msg)
    # Cerrar conexion
    cur.close()


#entrada
@app.route('/article/<string:id>/')
def article(id):
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entrada
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# Registro Form Class
class RegisterForm(Form):
    name = StringField('Nombre', [validators.Length(min=1, max=50)])
    username = StringField('Nombre de usuario', [validators.Length(min=4, max=25)])
    email = StringField('Correo electrónico', [validators.Length(min=6, max=50)])
    password = PasswordField('Contraseña', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Las contraseñas no coinciden')
    ])
    confirm = PasswordField('Confirmar contraseña')


# Registro de usuario
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Crear cursor
        cur = mysql.connection.cursor()

        # Ejecutar query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit a la base de datos
        mysql.connection.commit()

        # Cerrar conexion
        cur.close()

        flash('Listo, ahora puedes iniciar sesión', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# Inicio de sesion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Obtener Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Crear cursor
        cur = mysql.connection.cursor()

        # Obtener usuario por nombre de usuario
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Obtener hash
            data = cur.fetchone()
            password = data['password']

            # Comparar contraseñas
            if sha256_crypt.verify(password_candidate, password):
                # Aprobado
                session['logged_in'] = True
                session['username'] = username

                flash('Has iniciado sesión', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Inicio de sesión inválido'
                return render_template('login.html', error=error)
            # Cerrar conexion
            cur.close()
        else:
            error = 'Nombre de usuario no encontrado'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Revisar si se inicio sesion
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Por favor, inicia sesión para ingresar aquí', 'danger')
            return redirect(url_for('login'))
    return wrap

# Cerrar sesion
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('Has cerrado sesión', 'success')
    return redirect(url_for('login'))

# Mis entradas
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entradas
    #result = cur.execute("SELECT * FROM articles")
    # Mostrar entradas del usuario
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No se encontrado entradas'
        return render_template('dashboard.html', msg=msg)
    # Cerrar conexion
    cur.close()

# entrada Form Class
class ArticleForm(Form):
    title = StringField('Título', [validators.Length(min=1, max=200)])
    body = TextAreaField('Descripción', [validators.Length(min=30)])

# Agregar entrada
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Crear Cursor
        cur = mysql.connection.cursor()

        # Ejecutar
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit a la base de datos
        mysql.connection.commit()

        #Cerrar conexion
        cur.close()

        flash('Entrada creada', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Modificar entrada
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entrada por id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Obtener form
    form = ArticleForm(request.form)

    # entrada form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Crear Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Ejecutar
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit a la base de datos
        mysql.connection.commit()

        #Cerrar conexion
        cur.close()

        flash('Entrada actualizada', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Eliminar entrada
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Crear cursor
    cur = mysql.connection.cursor()

    # Ejecutar
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit a la base de datos
    mysql.connection.commit()

    #Cerrar conexion
    cur.close()

    flash('Entrada eliminada', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

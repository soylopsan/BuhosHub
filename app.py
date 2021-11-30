from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Configurar MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'buhoshub'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# Iniciar MYSQL
mysql = MySQL(app)


# Inicio
@app.route('/')
def index():
    return render_template('inicio.html')


# Acerca de
@app.route('/acerca')
def acerca():
    return render_template('acerca.html')


# Materias
@app.route('/materias')
def entradas():
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entradas
    result = cur.execute("SELECT * FROM entradas")

    entradas = cur.fetchall()

    if result > 0:
        return render_template('materias.html', entradas=entradas)
    else:
        msg = 'Aún no hay entradas'
        return render_template('materias.html', msg=msg)
    # Cerrar conexion
    cur.close()


# Materia
@app.route('/materia/<string:id>/')
def materia(id):
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entrada
    result = cur.execute("SELECT * FROM entradas WHERE id = %s", [id])

    entrada = cur.fetchone()

    return render_template('materia.html', entrada=entrada)


# Registrarse Form Class
class RegistrarseForm(Form):
    nombre = StringField('Nombre', [validators.Length(min=1, max=50)])
    nombreusuario = StringField('Nombre de usuario', [validators.Length(min=4, max=25)])
    correoelectronico = StringField('Correo electrónico', [validators.Length(min=6, max=50)])
    contrasena = PasswordField('Contraseña', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Las contraseñas no coinciden')
    ])
    confirm = PasswordField('Confirmar contraseña')


# Registro de usuario
@app.route('/registrarse', methods=['GET', 'POST'])
def registrarse():
    form = RegistrarseForm(request.form)
    if request.method == 'POST' and form.validate():
        nombre = form.nombre.data
        correoelectronico = form.correoelectronico.data
        nombreusuario = form.nombreusuario.data
        contrasena = sha256_crypt.encrypt(str(form.contrasena.data))

        # Crear cursor
        cur = mysql.connection.cursor()

        # Ejecutar query
        cur.execute("INSERT INTO usuarios(nombre, correoelectronico, nombreusuario, contrasena) VALUES(%s, %s, %s, %s)", (nombre, correoelectronico, nombreusuario, contrasena))

        # Commit a la base de datos
        mysql.connection.commit()

        # Cerrar conexion
        cur.close()

        flash('Listo, ahora puedes iniciar sesión', 'success')

        return redirect(url_for('iniciarSesion'))
    return render_template('registrarse.html', form=form)


# Inicio de sesion
@app.route('/iniciarsesion', methods=['GET', 'POST'])
def iniciarSesion():
    if request.method == 'POST':
        # Obtener Form Fields
        nombreusuario = request.form['nombreusuario']
        contra = request.form['contrasena']

        # Crear cursor
        cur = mysql.connection.cursor()

        # Obtener usuario por nombre de usuario
        result = cur.execute("SELECT * FROM usuarios WHERE nombreusuario = %s", [nombreusuario])

        if result > 0:
            # Obtener hash
            data = cur.fetchone()
            contrasena = data['contrasena']

            # Comparar contraseñas
            if sha256_crypt.verify(contra, contrasena):
                # Aprobado
                session['sesioniniciada'] = True
                session['nombreusuario'] = nombreusuario

                flash('Has iniciado sesión', 'success')
                return redirect(url_for('misEntradas'))
            else:
                error = 'Inicio de sesión inválido'
                return render_template('iniciarsesion.html', error=error)
            # Cerrar conexion
            cur.close()
        else:
            error = 'Nombre de usuario no encontrado'
            return render_template('iniciarsesion.html', error=error)

    return render_template('iniciarsesion.html')

# Revisar si se inicio sesion
def sesionIniciada(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'sesioniniciada' in session:
            return f(*args, **kwargs)
        else:
            flash('Por favor, inicia sesión para ingresar aquí', 'danger')
            return redirect(url_for('iniciarSesion'))
    return wrap

# Cerrar sesion
@app.route('/cerrarsesion')
@sesionIniciada
def cerrarSesion():
    session.clear()
    flash('Has cerrado sesión', 'success')
    return redirect(url_for('iniciarSesion'))

# Mis entradas
@app.route('/misentradas')
@sesionIniciada
def misEntradas():
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entradas
    #result = cur.execute("SELECT * FROM entradas")
    # Mostrar entradas del usuario
    result = cur.execute("SELECT * FROM entradas WHERE editor = %s", [session['nombreusuario']])

    entradas = cur.fetchall()

    if result > 0:
        return render_template('misentradas.html', entradas=entradas)
    else:
        msg = 'No se han encontrado entradas'
        return render_template('misentradas.html', msg=msg)
    # Cerrar conexion
    cur.close()

# entrada Form Class
class EntradaForm(Form):
    materia = StringField('Materia', [validators.Length(min=1, max=200)])
    descripcion = TextAreaField('Descripción', [validators.Length(min=30)])

# Agregar entrada
@app.route('/agregarentrada', methods=['GET', 'POST'])
@sesionIniciada
def agregarEntrada():
    form = EntradaForm(request.form)
    if request.method == 'POST' and form.validate():
        materia = form.materia.data
        descripcion = form.descripcion.data

        # Crear Cursor
        cur = mysql.connection.cursor()

        # Ejecutar
        cur.execute("INSERT INTO entradas(materia, descripcion, editor) VALUES(%s, %s, %s)",(materia, descripcion, session['nombreusuario']))

        # Commit a la base de datos
        mysql.connection.commit()

        #Cerrar conexion
        cur.close()

        flash('Entrada creada', 'success')

        return redirect(url_for('misEntradas'))

    return render_template('agregarentrada.html', form=form)


# Modificar entrada
@app.route('/modificarentrada/<string:id>', methods=['GET', 'POST'])
@sesionIniciada
def modificarEntrada(id):
    # Crear cursor
    cur = mysql.connection.cursor()

    # Obtener entrada por id
    result = cur.execute("SELECT * FROM entradas WHERE id = %s", [id])

    entrada = cur.fetchone()
    cur.close()
    # Obtener form
    form = EntradaForm(request.form)

    # entrada form fields
    form.materia.data = entrada['materia']
    form.descripcion.data = entrada['descripcion']

    if request.method == 'POST' and form.validate():
        materia = request.form['materia']
        descripcion = request.form['descripcion']

        # Crear Cursor
        cur = mysql.connection.cursor()
        app.logger.info(materia)
        # Ejecutar
        cur.execute ("UPDATE entradas SET materia=%s, descripcion=%s WHERE id=%s",(materia, descripcion, id))
        # Commit a la base de datos
        mysql.connection.commit()

        #Cerrar conexion
        cur.close()

        flash('Entrada actualizada', 'success')

        return redirect(url_for('misEntradas'))

    return render_template('modificarentrada.html', form=form)

# Eliminar entrada
@app.route('/eliminarentrada/<string:id>', methods=['POST'])
@sesionIniciada
def eliminarEntrada(id):
    # Crear cursor
    cur = mysql.connection.cursor()

    # Ejecutar
    cur.execute("DELETE FROM entradas WHERE id = %s", [id])

    # Commit a la base de datos
    mysql.connection.commit()

    #Cerrar conexion
    cur.close()

    flash('Entrada eliminada', 'success')

    return redirect(url_for('misEntradas'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)

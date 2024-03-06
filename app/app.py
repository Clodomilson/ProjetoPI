from flask import Flask, render_template, request, redirect, url_for, session, flash, request
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email
from passlib.hash import sha256_crypt
from werkzeug.utils import secure_filename
import mysql.connector
import os
import requests


app = Flask(__name__)


app.secret_key = 'malucoFotografoSenac2024'

# Função para fazer upload de imagem para o FreeImage.Host
def upload_image_to_freeimagehost(image_file):
    API_KEY = '6d207e02198a847aa98d0a2a901485a5'
    UPLOAD_URL = 'https://freeimage.host/api/1/upload'

    files = {'source': image_file}
    data = {'key': API_KEY, 'action': 'upload', 'format': 'json'}

    response = requests.post(UPLOAD_URL, files=files, data=data)

    if response.status_code == 200:
        response_data = response.json()
        image_url = response_data['image']['url']
        return image_url
    else:
        return None



# Conexão com o banco de dados
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="", 
)

# Cursor para executar consultas SQL
cursor_master = db.cursor()

# Obtém o caminho absoluto para o arquivo SQL
db_dir = os.path.join(os.path.dirname(__file__), 'db')
sql_file = os.path.join(db_dir, 'banco.sql')

# Executa os comandos SQL do arquivo
with open(sql_file, 'r') as file:
    sql_script = file.read()

sql_commands = sql_script.split(';')

# Executa cada comando SQL individualmente
for command in sql_commands:
    if command.strip(): 
        cursor_master.execute(command)

db.commit()
cursor_master.close()

# Conexão com o banco de dados
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # Substitua pela senha do seu banco de dados MySQL
    database="visual"
)
cursor = db.cursor()

# Define o formulário de registro
class RegistrationForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    sobrenome = StringField('Sobrenome', validators=[DataRequired()])
    nome_usuario = StringField('Nome de Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    foto_perfil = FileField('Foto de Perfil', validators=[FileAllowed(['jpg', 'png'], 'Apenas imagens JPG ou PNG são permitidas.')])
    submit = SubmitField('Registrar')

# Define o formulário de login
class LoginForm(FlaskForm):
    nome_usuario = StringField('Nome de Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

# Define o formulário de perfil
class ProfileForm(FlaskForm):
    nome = StringField('Nome', validators=[DataRequired()])
    sobrenome = StringField('Sobrenome', validators=[DataRequired()])
    nome_usuario = StringField('Nome de Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Biografia')
    url = StringField('URL')
    rua = StringField('Rua')
    cidade = StringField('Cidade')
    estado = StringField('Estado')
    pais = StringField('País')
    codigo_postal = StringField('Código Postal')
    submit = SubmitField('Salvar')

# Página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Página 'Quem Somos'
@app.route('/quemsomos')
def quemsomos():
    return render_template('quemsomos.html')


# Pagina de Registro
# Pagina de Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    foto_perfil_url = None  # Inicializa foto_perfil_url como None
    if form.validate_on_submit():
        # Obtenha outros dados do formulário
        nome = form.nome.data
        sobrenome = form.sobrenome.data
        nome_usuario = form.nome_usuario.data
        senha = sha256_crypt.hash(form.senha.data)
        telefone = form.telefone.data
        email = form.email.data
        
        # Verifica se a foto de perfil foi fornecida
        if form.foto_perfil.data:
            # Faz upload da imagem para o FreeImage.Host
            foto_perfil_url = upload_image_to_freeimagehost(form.foto_perfil.data)
        
        # Insira o usuário no banco de dados, incluindo o URL da imagem do perfil, se disponível
        cursor.execute("INSERT INTO perfilFotografos (nome, sobrenome, nome_usuario, senha, telefone, email, foto_perfil) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (nome, sobrenome, nome_usuario, senha, telefone, email, foto_perfil_url))
        db.commit()
        
        flash('Cadastro realizado com sucesso! Faça login para acessar sua conta.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)







# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        nome_usuario = form.nome_usuario.data
        senha_candidate = form.senha.data
        
        cursor.execute("SELECT * FROM perfilFotografos WHERE nome_usuario = %s", (nome_usuario,))
        account = cursor.fetchone()
        
        if account:
            senha = account[4]
            if sha256_crypt.verify(senha_candidate, senha):
                session['loggedin'] = True
                session['id'] = account[0]
                session['nome_usuario'] = account[3]
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('profile'))
            else:
                flash('Senha incorreta. Tente novamente.', 'danger')
        else:
            flash('Usuário não encontrado.', 'danger')
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('nome_usuario', None)
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

# Página de perfil
@app.route('/profile')
def profile():
    if 'loggedin' in session:
        user_id = session['id']
        cursor.execute("SELECT * FROM perfilFotografos WHERE id = %s", (user_id,))
        profile_data = cursor.fetchone()  # Lê os resultados da consulta

        # Verifica se os dados do perfil foram encontrados
        if profile_data:
            # Retorna os dados do perfil para a página de perfil
            return render_template('profile.html', profile_data=profile_data)
        else:
            # Se os dados do perfil não forem encontrados, exibe uma mensagem de erro
            flash('Dados do perfil não encontrados.', 'danger')
            return render_template('error.html', message='Dados do perfil não encontrados')
    else:
        # Se o usuário não estiver logado, redireciona para a página de login
        flash('Você precisa fazer login para acessar esta página.', 'danger')
        return redirect(url_for('login'))

# Página de edição de perfil
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    form = ProfileForm()
    if 'loggedin' in session:
        user_id = session['id']
        if form.validate_on_submit():
            nome = form.nome.data
            sobrenome = form.sobrenome.data
            nome_usuario = form.nome_usuario.data
            senha = sha256_crypt.hash(form.senha.data)
            telefone = form.telefone.data
            email = form.email.data
            bio = form.bio.data
            url = form.url.data
            rua = form.rua.data
            cidade = form.cidade.data
            estado = form.estado.data
            pais = form.pais.data
            codigo_postal = form.codigo_postal.data
            
            cursor.execute("UPDATE perfilFotografos SET nome = %s, sobrenome = %s, nome_usuario = %s, senha = %s, telefone = %s, email = %s, bio = %s, url = %s, rua = %s, cidade = %s, estado = %s, pais = %s, codigo_postal = %s WHERE id = %s",
                           (nome, sobrenome, nome_usuario, senha, telefone, email, bio, url, rua, cidade, estado, pais, codigo_postal, user_id))
            db.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('profile'))
        return render_template('edit_profile.html', form=form)
    else:
        flash('Você precisa fazer login para acessar esta página.', 'danger')
        return redirect(url_for('login'))


# Página do portfólio
@app.route('/<nome_usuario>/portfolio')
def portfolio(nome_usuario):
    if 'loggedin' in session:
        cursor.execute("SELECT * FROM perfilFotografos WHERE nome_usuario = %s", (nome_usuario,))
        profile_data = cursor.fetchone()

        if profile_data:
            nome = profile_data[1]  # Índice para o primeiro nome
            sobrenome = profile_data[2]  # Índice para o sobrenome
            return render_template('portfolio.html', nome=nome, sobrenome=sobrenome)
        else:
            flash('Perfil não encontrado.', 'danger')
            return render_template('error.html', message='Perfil não encontrado')
    else:
        flash('Você precisa fazer login para acessar esta página.', 'danger')
        return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port= 5000)

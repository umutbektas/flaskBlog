from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

#user login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görmek için giriş yapınız !", "warning")
            return redirect(url_for("login", next=request.url))
    return decorated_function

#user register form class
class RegisterForm(Form):
    name = StringField("İsim Soyisim:", validators=[validators.Length(min=4, max=25,message="İsim alanı Min:4 Max:25 karakter olmalıdır."), validators.DataRequired(message="İsim alanı boş geçilemez.")])
    username = StringField("Kullanıcı Adı:", validators=[validators.Length(min=3, max=25, message="Kullanıcı Adı Min:3 Max:25 karakter olmalıdır."), validators.DataRequired(message="Kullanıcı Adı boş geçilemez.")])
    email = StringField("E-Mail:", validators=[validators.Length(min=8, max=25, message="E-Mail Min:8 Max:25 karakter olmalıdır."), validators.DataRequired(message="E-mail alanı boş geçilemez."), validators.Email(message="Lütfen geçerli bir email giriniz.")])
    password = PasswordField("Parola:", validators=[
        validators.DataRequired(message="Parola giriniz."),
        validators.EqualTo(fieldname="passconfirm", message="Parolalar uyuşmuyor.")
    ])
    passconfirm = PasswordField("Parola Doğrula", validators=[validators.DataRequired(message="Doğrulama Parolası giriniz.")])

#user login form class
class LoginForm(Form):
    username = StringField("Kullanıcı Adı:", validators=[validators.DataRequired("Kullanıcı Adı boş geçilemez.") ])
    password = PasswordField("Parola:", validators=[validators.DataRequired(message="Parola boş geçilemez.")])


class ArticleForm(Form):
    title = StringField("Makale Başlığı:", validators=[validators.DataRequired(message="Başlık boş geçilemez."), validators.Length(min=5, max=50, message="Başlık min:5, max:50 karater olmalıdır.")])
    content = TextAreaField("İçerik:", validators=[validators.Length(min=10, message="Min: 10 karakter olmalıdır."), validators.DataRequired(message="İçeik boş geçilemez.")])


app = Flask(__name__)
app.secret_key = "uBlog"

#mysql parameters
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "fblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

#mysql connection
mysql = MySQL(app)

#routes
@app.route('/')
def index():
    sozluk = dict()
    sozluk['title'] = "Ana Sayfa"
    sozluk['body'] = "Umut Bektaş"
    return render_template("index.html",sozluk = sozluk)

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/dashboard')
@login_required
def dashboard():
    username = session["username"]
    cursor = mysql.connection.cursor()
    sqlquery = "SELECT * FROM articles where author = %s"
    result = cursor.execute(sqlquery, (username,))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles=articles)
    else:
        return render_template("dashboard.html")

@app.route('/articles')
def articles():
    cursor = mysql.connection.cursor()
    sqlquery = "SELECT * FROM articles"
    result = cursor.execute(sqlquery)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles=articles)
    else:
         return render_template("articles.html")

#article detail page
@app.route('/articles/<string:id>')
def detail(id):
    cursor = mysql.connection.cursor()
    sqlquery = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(sqlquery, (id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("articledetail.html", article=article)
    else:
        return render_template("articledetail.html")



@app.route('/articles/edit/<string:id>', methods = ["GET", "POST"])
@login_required
def edit(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        username = session["username"]
        sqlquery = "SELECT * FROM articles WHERE id = %s AND author = %s"
        result = cursor.execute(sqlquery, (id,username))

        if result > 0:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("articleedit.html", form=form)
        else:
            flash("Bu makale yok veya size ait değil.")
            return redirect(url_for("dashboard"))
    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sqlquery2 = "UPDATE articles SET title = %s, content = %s WHERE id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sqlquery2, (newTitle, newContent, id))
        mysql.connection.commit()
        flash("Başarıyla Güncellendi", "success")
        return redirect(url_for("dashboard"))

        pass
@app.route('/articles/delete/<string:id>')
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    username = session["username"]
    sqlquery = "SELECT * FROM articles WHERE id = %s AND author = %s"

    result = cursor.execute(sqlquery, (id, username))

    if result > 0:
        deletequery = "DELETE FROM articles WHERE id = %s"
        cursor.execute(deletequery, (id,))
        mysql.connection.commit()
        flash("Başarıyla silindi !", "success")
        return redirect(url_for("dashboard"))

    else:
        flash("Silinemedi, böyle bir makale bulunmuyor veya size ait değil.", "danger")
        return redirect(url_for("dashboard"))


@app.route('/register', methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        #form data variables
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        #mysql cursor and register query
        cursor = mysql.connection.cursor()
        sqlquery = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        #mysql register user
        cursor.execute(sqlquery,(name,email,username,password))
        #mysql register changes commit
        mysql.connection.commit()
        #mysql close
        cursor.close()
        flash("Kayıt başarılı Hoş Geldin!, şimdi giriş yapabilirsin.", "success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html", form=form)

@app.route('/login', methods= ["GET", "POST"])
def login():
    #login form create
    form = LoginForm(request.form)

    #form validate
    if request.method == "POST" and form.validate():
        username = form.username.data
        password = form.password.data

        #mysql connection
        cursor = mysql.connection.cursor()

        #is username exist ? query
        sqlquery = "SELECT * FROM users where username = %s"
        result = cursor.execute(sqlquery, (username,))

        #username exist
        if result > 0:
            data = cursor.fetchone()
            real_pass = data["password"]

            #is password equivalent ?
            if sha256_crypt.verify(password, real_pass):
                flash("Başarıyla giriş yaptınız !", "success")
                session["logged_in"] = True
                session["username"] = username
                session["name"] = data["name"]

                if request.args.get('next'):
                    return redirect(request.args.get('next'))
                else:
                    return redirect(url_for("index"))
            else:
                flash("Yanlış parola, tekrar deneyin !", "warning")
                return redirect(url_for("login"))
        else:
            #username doesn't exist
            flash("Kullanıcı bulunamadı !", "warning")
            return redirect(url_for("login"))
    else:
        #form validate fail
        return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    if session["logged_in"]:
        session.clear()
        flash("Başarıyla çıkış yaptınız !", "success")
        return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))


@app.route("/addarticle", methods=["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        author = session["username"]

        cursor = mysql.connection.cursor()

        sqlquery = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sqlquery, (title,author,content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale başarı ile eklendi !", "success")
        return redirect(url_for("dashboard"))

    else:
        return render_template("addarticle.html", form=form)


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        searchkey = request.form.get("searchkey")
        cursor = mysql.connection.cursor()
        pass

#run app
if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from data import db_session, news, users, menu
from werkzeug.utils import secure_filename
import news_api
import json, pprint, os
import datetime as dt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
login_manager = LoginManager()
login_manager.init_app(app)
UPLOAD_FOLDER = 'static/img/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@login_manager.user_loader
def load_user(user_id):
    sessions = db_session.create_session()
    return sessions.query(users.User).get(user_id)


class RegisterForm(FlaskForm):
    email = StringField('&#9993; Почта', validators=[DataRequired()])
    password = PasswordField('&#128274; Пароль', validators=[DataRequired()])
    password_again = PasswordField('&#128274; Повторите пароль', validators=[DataRequired()])
    name = StringField('Имя пользователя', validators=[DataRequired()])
    city = TextAreaField("Ваш город ")
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    email = StringField("&#9993; Почта", validators=[DataRequired()])
    password = PasswordField('&#128274; Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField('Содержание')
    is_private = BooleanField('Приватность')
    submit = SubmitField('Применить')


class AddInOrder(FlaskForm):
    submit = SubmitField('Добавить')


class MenuForm(FlaskForm):
    group = StringField("Вид блюда", validators=[DataRequired()])
    title = StringField("Название блюда", validators=[DataRequired()])
    content = StringField("Состав блюда", validators=[DataRequired()])
    price = StringField("Цена блюда", validators=[DataRequired()])
    submit = SubmitField('Добавить')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/yours-order", methods=['GET', 'POST'])
def yours_order():
    form = MenuForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        print(form.group.data, form.title.data, form.content.data, form.price.data)
        if sessions.query(menu.Menu).filter(menu.Menu.title == form.title.data).first():
            return render_template('newfood.html', title='Добавление блюда',
                                   form=form,
                                   message="Такое блюдо уже есть")

        menus = menu.Menu(
            group=form.group.data,
            title=form.title.data,
            content=form.content.data,
            price=form.price.data,
            picture='static/img/nophoto.png'
        )
        sessions.add(menus)
        sessions.commit()
        return redirect('/add-picture-on-food')
    return render_template('newfood.html', title='Добавление блюда', form=form)


@app.route("/add-picture-on-food", methods=['GET', 'POST'])
def write_new_food():
    if request.method == 'GET':
        return render_template('add_picture.html')
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            session = db_session.create_session()
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
                menu.picture = UPLOAD_FOLDER + filename
                session.merge(menu)
                session.commit()
            except Exception:
                pass
            return redirect('/menu')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/news', methods=['GET', 'POST'])
@login_required
def add_news():
    form = NewsForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        new = news.News()
        new.title = form.title.data
        new.content = form.content.data
        new.is_private = form.is_private.data
        current_user.news.append(new)
        sessions.merge(current_user)
        sessions.commit()
        return redirect('/')
    return render_template('news.html', title='Добавление новости', form=form)


@app.route('/news_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def news_delete(id):
    sessions = db_session.create_session()
    new = sessions.query(news.News).filter(news.News.id == id,
                                           news.News.user == current_user).first()
    if new:
        sessions.delete(new)
        sessions.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/news/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_news(id):
    form = NewsForm()
    if request.method == 'GET':
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id,
                                               news.News.user == current_user).first()
        if new:
            form.title.data = new.title
            form.content.data = new.content
            form.is_private.data = new.is_private
        else:
            abort(404)
    if form.validate_on_submit():
        sessions = db_session.create_session()
        new = sessions.query(news.News).filter(news.News.id == id,
                                               news.News.user == current_user).first()
        if new:
            new.title = form.title.data
            new.content = form.content.data
            new.is_private = form.is_private.data
            sessions.commit()
            return redirect('/')
        else:
            abort(404)
    return render_template('news.html', title='Редактирование новости', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        user = sessions.query(users.User).filter(users.User.email == form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user, remember=form.remember_me.data)
            return redirect('/')
        return render_template('login.html', message='Неправильный логин или пароль', form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route("/cookie_test")
def cookie_test():
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response(f'Вы пришли на эту страницу {visits_count + 1} раз')
        res.set_cookie("visits_count", str(visits_count + 1), max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response('Вы пришли на эту страницу в первый раз за 2 года')
        res.set_cookie("visits_count", "1", max_age=60 * 60 * 24 * 365 * 2)
    return res


@app.route('/session_test')
def session_test():
    session.permanent = True
    session['visits_count'] = session.get('visits_count', 0) + 1
    return f"Вы зашли на страницу {session['visits_count']} раз!"


@app.route("/")
@app.route("/index")
def index():
    sessions = db_session.create_session()
    new = sessions.query(news.News).filter(news.News.is_private != True)
    params = {}
    params['title'] = 'MeToo'
    params['arr_picture'] = ['akthii.jpg', 'new.jpg', 'first_purchase.png']
    params['admin'] = 'no'
    return render_template("karysel.html", **params)


@app.route("/admin", methods=['GET', 'POST'])
@app.route("/index-admin", methods=['GET', 'POST'])
def index_for_admin():
    sessions = db_session.create_session()
    new = sessions.query(news.News).filter(news.News.is_private != True)
    params = {}
    params['title'] = 'MeToo'
    params['arr_picture'] = ['akthii.jpg', 'new.jpg', 'first_purchase.png']
    params['admin'] = 'yes'
    if request.method == 'GET':
        return render_template('karysel.html', **params)
    elif request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            params['arr_picture'].append(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return render_template("karysel.html", **params)


@app.route('/menu', methods=['POST', 'GET'])
def menu_func():
    form = AddInOrder()
    with open("menu.json", "rt", encoding="utf8") as f:
        menu = json.loads(f.read())
    if form.validate_on_submit():
        return redirect('/login')
    return render_template('menu.html', spisok_poz=list(menu.keys()), pizza_menu=menu, form=form)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        sessions = db_session.create_session()
        if sessions.query(users.User).filter(users.User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = users.User(
            name=form.name.data,
            password=form.password.data,
            email=form.email.data,
            city=form.city.data
        )
        user.set_password(form.password.data)
        sessions.add(user)
        sessions.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def main():
    db_session.global_init('db/menu.sqlite')
    app.run()


if __name__ == '__main__':
    main()

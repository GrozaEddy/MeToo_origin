from flask import Flask, render_template, redirect, request, make_response, session, abort, jsonify
from flask_wtf import FlaskForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired
from data import db_session, news, users, menu, history
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


class AddInHistory(FlaskForm):
    city = StringField('В какой город доставить?', validators=[DataRequired()])
    full_name_street = StringField('Полный адрес(не забудьте указать номер дома и квартиры)',
                       validators=[DataRequired()])


class Korzina(FlaskForm):
    submit = SubmitField('Корзина')


class MenuForm(FlaskForm):
    group = StringField("Вид блюда", validators=[DataRequired()])
    title = StringField("Название блюда", validators=[DataRequired()])
    content = StringField("Состав блюда", validators=[DataRequired()])
    price = StringField("Цена блюда", validators=[DataRequired()])
    submit = SubmitField('Добавить')


class KorzinaForm(FlaskForm):
    place = StringField('Адрес для доставки:', validators=[DataRequired()])
    number = StringField('Ваш номер телефона:', validators=[DataRequired()])
    submit = SubmitField('Оплатить')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route("/addfood", methods=['GET', 'POST'])
def add_food():
    form = MenuForm()
    if form.validate_on_submit():
        sessions = db_session.create_session()
        if sessions.query(menu.Menu).filter(menu.Menu.title == form.title.data).first():
            return render_template('newfood.html', title='Добавление блюда',
                                   form=form,
                                   message="Такое блюдо уже есть")

        return redirect(f'/add-picture-on-food/{form.group.data}/{form.title.data}/'
                        f'{form.content.data}/{form.price.data}')
    return render_template('newfood.html', title='Добавление блюда', form=form)


@app.route("/add-picture-on-food/<string:group>/<string:title>/<string:content>/<string:price>",
           methods=['GET', 'POST'])
def write_new_food(group, title, content, price):
    print(group, title, content, price)
    if request.method == 'GET':
        return render_template('add_picture.html')
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            session = db_session.create_session()
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            try:
                file_name = '/'.join([UPLOAD_FOLDER, filename])
                menus = menu.Menu(
                    group=group,
                    title=title,
                    content=content,
                    price=price,
                    picture=file_name
                )
                session.add(menus)
                session.commit()
            except Exception:
                print(menu.Menu.picture)
            return redirect('/menu')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


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


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = Korzina()
    if form.validate_on_submit():
        print(1)
        return redirect('/')  # здесь нужно прописать путь к корзине, но не работает
    return render_template('profile.html', form=form)


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


@app.route('/menubuy/<string:idd>')
def menu_buy(idd):
    sessions = db_session.create_session()
    user = sessions.query(users.User).get(current_user.id)
    if user.order is None:
        user.order = ''
    if idd not in str(user.order).split():
        user.order = str(user.order) + ' ' + idd
    sessions.commit()
    return redirect('/menu')


@app.route('/menu', methods=['POST', 'GET'])
def menu_func():
    form = AddInOrder()
    sessions = db_session.create_session()
    menu_arr = {}
    for x in sessions.query(menu.Menu).all():
        if x.group.upper() not in menu_arr.keys():
            menu_arr[x.group.upper()] = [{
                'id': x.id,
                'name': x.title,
                'sostav': x.content,
                'price': x.price,
                'picture_place': x.picture
            }
            ]
        else:
            menu_arr[x.group.upper()].append({
                'id': x.id,
                'name': x.title,
                'sostav': x.content,
                'price': x.price,
                'picture_place': x.picture
            })
    return render_template('menu.html', spisok_poz=list(menu_arr.keys()), pizza_menu=menu_arr,
                           form=form)


@app.route('/plus/<string:idd>')
def plus_in_order(idd):
    sessions = db_session.create_session()
    user = sessions.query(users.User).get(current_user.id)
    user.order = str(user.order) + ' ' + idd.strip()
    sessions.commit()
    return redirect('/yours-order')


@app.route('/minus/<string:idd>')
def minus_in_order(idd):
    sessions = db_session.create_session()
    user = sessions.query(users.User).get(current_user.id)
    arr = user.order.split()
    if idd.strip() in arr and arr.count(idd) > 1:
        arr.remove(idd.strip())
    arr.sort()
    user.order = ' '.join(arr)
    sessions.commit()
    return redirect('/yours-order')


@app.route('/delete/<string:idd>')
def delete(idd):
    sessions = db_session.create_session()
    user = sessions.query(users.User).get(current_user.id)
    arr = str(user.order).split()
    if len(arr) != 0:
        new_arr_order = []
        for x in sorted(arr):
            if x != idd:
                new_arr_order.append(x)
        user.order = ' '.join(new_arr_order)
        sessions.commit()
        return redirect('/yours-order')
    return redirect('/menu')


@app.route('/add-order', methods=['POST', 'GET'])
def add_order():
    form = KorzinaForm()
    sessions = db_session.create_session()
    user = sessions.query(users.User).get(current_user.id)
    price = 0
    arr = str(user.order).split()
    for x in sorted(arr):
        for y in sessions.query(menu.Menu).filter(menu.Menu.id == x):
            price += (arr.count(x) * int(y.price))
    if form.validate_on_submit():
        user_answer = request.form['opl']
        print(user_answer)
        add_in_history = history.History(
            user_id=user.id,
            address='address',
            about_order=user.order,
            all_price=price
        )
        user.order = ''
        sessions.add(add_in_history)
        sessions.commit()
        if user_answer == 'qiwi':
            return redirect('https://qiwi.com/')
        else:
            return redirect('https://www.paypal.com/')
    return render_template('oplata.html', form=form, price=price)


@app.route('/yours-order', methods=['POST', 'GET'])
def yours_order():
    sessions = db_session.create_session()
    user = sessions.query(users.User).get(current_user.id)
    arr = str(user.order).split()
    menu_arr = {}
    arr_id = []
    for y in sorted(arr):
        for x in sessions.query(menu.Menu).filter(menu.Menu.id == y):
            if x.id not in arr_id:
                if x.group.upper() not in menu_arr.keys():
                    menu_arr[x.group.upper()] = [{
                        'id': x.id,
                        'name': x.title,
                        'sostav': x.content,
                        'price': x.price,
                        'picture_place': x.picture,
                        'count': arr.count(y)
                    }
                    ]
                else:
                    menu_arr[x.group.upper()].append({
                        'id': x.id,
                        'name': x.title,
                        'sostav': x.content,
                        'price': x.price,
                        'picture_place': x.picture,
                        'count': arr.count(y)
                    })
            arr_id.append(x.id)
    return render_template('korzina.html', spisok_poz=list(menu_arr.keys()), pizza_menu=menu_arr,
                           user_id=user.id, count=len(menu_arr.keys()))


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

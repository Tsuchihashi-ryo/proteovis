from flask import Flask,render_template, request, redirect, url_for, session,flash

from flask_login import LoginManager,current_user, login_user
from werkzeug.security import generate_password_hash
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import urlparse
from models import *
from forms import *

import os


def create_app():
    app = Flask(__name__,static_folder='./static', static_url_path='/static')

    # Load configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-hard-to-guess-string')
    app.config['GCS_BUCKET_NAME'] = os.environ.get('GCS_BUCKET_NAME')

    # Use DATABASE_URL from environment variable, with a fallback to local SQLite
    default_db_uri = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', default_db_uri)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.jinja_env.auto_reload = True

    db.init_app(app)

    login = LoginManager()
    login.init_app(app)
    login.login_view = 'login'
    login.login_message_category = 'info'


    with app.app_context():
        db.create_all()



    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    # ユーザー登録ページのルーティング
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        # 現在のユーザーが有効な権限を保持している(ログインしている)場合
        if current_user.is_authenticated:
            # トップページにリダイレクト
            return redirect(url_for('main.index'))
        # forms.pyで定義したRegistrationFormを読み込み
        form = RegistrationForm()
        # 入力値のバリデーションチェックを通過した場合
        if form.validate_on_submit():
            # 入力値を元に新しくUserクラスのインスタンスを作成する
            user = User(name=form.name.data, 
                        password=generate_password_hash(form.password.data),
                        email=form.email.data)
            # DBのusersテーブルに作成したインスタンスの情報をレコードとして追加
            db.session.add(user)
            # レコードの登録を確定
            db.session.commit()
            # 登録に成功した旨のflashを表示
            flash('Congratulations, you are now a registered user!')
            # loginページにリダイレクト
            return redirect(url_for('login'))
        # ユーザーが未ログインまたはバリデーションエラーの場合、ユーザー登録ページにリダイレクト
        return render_template('register.html', title='Register', form=form)


    # loginページのルーティング
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # 現在のユーザーが有効な権限を保持している(ログインしている)場合
        if current_user.is_authenticated:
            # トップページにリダイレクト
            return redirect(url_for('main.index'))
        # forms.pyで定義するloginフォームを読み込む
        form = LoginForm()
        # wtf? validate_on_submitとは
        if form.validate_on_submit():
            # ログインしようとしているユーザーのレコードを取得
            user = User.query.filter_by(email=form.email.data).one_or_none()
            # ユーザーが存在しない、もしくはパスワードが一致しない場合
            # (check_passwordはUserクラスで定義した関数)
            if user is None or not user.check_password(form.password.data):
                # usernameまたはpasswordが誤っている旨のflashを表示
                flash('Invalid username or password')
                # loginページへリダイレクト
                return redirect(url_for('login'))
            # loginユーザーとして取得したユーザーの情報を登録
            login_user(user, remember=form.remember_me.data)
            # 本機能実装前に記述していたトップページへのリダイレクトは不要なので削除する
            # return redirect(url_for('index'))
            # ログイン後の遷移先(アクセスしようとしていたページ)のurlを取得
            next_page = request.args.get('next')
            # 遷移先が存在しない場合もしくはそのurlのnetloc(ファーストレベルのドメイン)がある場合
            if not next_page or urlparse(next_page).netloc != '': #or url_parse(next_page).netloc != '':
                # トップページにリダイレクト
                next_page = url_for('main.index')
            # アクセスしようとしていたページにリダイレクトバック
            return redirect(next_page)

        # loginページのテンプレートを返す
        return render_template('login.html', title='Sign In', form=form)




    # blueprint for non-auth parts of app
    from app import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
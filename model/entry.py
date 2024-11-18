from app import app, db


if __name__ == '__main__':
    with app.app_content:
        db.create_all()
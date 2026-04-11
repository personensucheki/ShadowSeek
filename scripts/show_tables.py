from app import create_app
from app.extensions import db

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print(db.inspect(db.engine).get_table_names())

import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from backend.database import configure_db, db
from backend.routes import index_routes, login_routes, cadastrar_routes

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

configure_db(app)

from backend.user import Usuario, Chat, Message  # noqa: F401, E402

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "index_routes.index"


@login_manager.user_loader
def load_user(user_id):
    return Usuario.get_by_id(int(user_id))


app.register_blueprint(index_routes)
app.register_blueprint(login_routes)
app.register_blueprint(cadastrar_routes)


def _migrate_schema():
    """Adiciona colunas novas em tabelas já existentes (SQLite não suporta ALTER sem isso)."""
    from sqlalchemy import text, inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    migrations = {
        'chats':    [('created_at', 'DATETIME')],
        'messages': [('created_at', 'DATETIME')],
    }

    with db.engine.connect() as conn:
        for table, columns in migrations.items():
            if table not in tables:
                continue
            existing = {c['name'] for c in inspector.get_columns(table)}
            for col_name, col_type in columns:
                if col_name not in existing:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                    ))
        conn.commit()


with app.app_context():
    db.create_all()
    _migrate_schema()

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask
from .extensions import db, migrate




def create_app(config_class=None):
        # CSRF-Token für alle Templates bereitstellen
        @app.context_processor
        def inject_csrf_token():
            from flask_wtf.csrf import generate_csrf
            return dict(csrf_token=generate_csrf())
    app = Flask(__name__)
    if config_class:
        app.config.from_object(config_class)
    else:
        from .config import DevConfig
        app.config.from_object(DevConfig)


    db.init_app(app)
    migrate.init_app(app, db)
    from .extensions import csrf
    csrf.init_app(app)




    # Blueprints registrieren
    from .routes.auth import auth_bp
    from .routes.search import search_bp
    from .routes.admin import admin_bp
    from .routes.health import health_bp
    from .routes.chatbot import chatbot_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(chatbot_bp)

    return app

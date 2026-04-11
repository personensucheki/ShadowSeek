from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import CSRFProtect

# Alle Extensions zentral initialisieren
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()

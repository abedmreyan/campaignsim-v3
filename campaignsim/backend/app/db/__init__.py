"""SQLAlchemy database instance.

Import `db` from here in models and wherever session access is needed.
Never import db directly from flask_sqlalchemy.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

import os

class Config:
    # ...
    STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    DATABASE_URL=sqlite:////data/db/presidentigami.db

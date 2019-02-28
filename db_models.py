#import os
#import sys
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from app import app, db

#db.metadata.clear()
class UserEvents(db.Model):
    __tablename__ = 'user_events'

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.String(80))
    time = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return '<UserEvent %r>' % self.id
from datetime import datetime, timezone
from flask_login import UserMixin
from .database import db


class Usuario(UserMixin, db.Model):
    __tablename__ = 'users'

    id       = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    chats    = db.relationship('Chat', backref='user', lazy=True, cascade='all, delete-orphan')

    @property
    def nome_usuario(self):
        return self.username

    @staticmethod
    def get_by_id(user_id):
        return db.session.get(Usuario, user_id)

    @staticmethod
    def obter_chats_usuario(user_id):
        chats = Chat.query.filter_by(user_id=user_id).order_by(Chat.created_at.desc()).all()
        return [(c.id, c.title, c.user_id) for c in chats]


class Chat(db.Model):
    __tablename__ = 'chats'

    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(255), default='Nova Conversa')
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    messages   = db.relationship('Message', backref='chat', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':        self.id,
            'title':     self.title or 'Sem título',
            'timestamp': self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
        }


class Message(db.Model):
    __tablename__ = 'messages'

    id            = db.Column(db.Integer, primary_key=True)
    text_usuario  = db.Column(db.Text)
    text_servidor = db.Column(db.Text)
    created_at    = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    chat_id       = db.Column(db.Integer, db.ForeignKey('chats.id'), nullable=False)

    def to_dict(self):
        return {
            'id':        self.id,
            'usuario':   self.text_usuario,
            'servidor':  self.text_servidor,
        }

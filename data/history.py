import sqlalchemy
from data.base import SqlAlchemyBase


class History(SqlAlchemyBase):
    __tablename__ = 'history'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    user_name = sqlalchemy.Column(sqlalchemy.String)
    link = sqlalchemy.Column(sqlalchemy.String, unique=True)

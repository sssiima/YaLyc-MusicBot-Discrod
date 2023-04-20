import sqlalchemy
from data.base import SqlAlchemyBase


class Names(SqlAlchemyBase):
    __tablename__ = 'name'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           autoincrement=True)
    track_name = sqlalchemy.Column(sqlalchemy.String)
    link = sqlalchemy.Column(sqlalchemy.String, unique=True)
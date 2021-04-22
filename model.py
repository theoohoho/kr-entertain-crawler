from sqlalchemy import Column, Integer
from sqlalchemy.types import VARCHAR, Text
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class TV_CHANNEL(Base):
    __tablename__ = 'tv_channel'
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(10))


class TV_SHOW(Base):
    __tablename__ = 'tv_show'
    id = Column(Integer, primary_key=True)
    title = Column(VARCHAR(40))
    description = Column(Text)
    tv_channel_id = Column(Integer)


class TV_EPISODE(Base):
    __tablename__ = 'tv_episode'
    id = Column(Integer, primary_key=True)
    name = Column(VARCHAR(40))
    publish_date = Column(VARCHAR(20))
    tv_show_id = Column(Integer)
    source_link = Column(Text)

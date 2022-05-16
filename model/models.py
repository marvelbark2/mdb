"""Models module"""
import os.path
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

db_file = f'sqlite:///{os.path.dirname(os.path.abspath("__file__"))}/data/db/mdb.db'
engine = create_engine(db_file, poolclass=QueuePool)

Base = declarative_base(name="Model")
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

class Region(Base):
    """Class Region"""
    __tablename__ = "region"
    id = Column(Integer, primary_key=True, autoincrement=True)
    department_code = Column(Integer)
    department_name = Column(String)

class Parti(Base):
    """Class Parti"""
    __tablename__ = "parti"
    id = Column(Integer, primary_key=True)
    parti_name = Column(String)
    candidat = relationship

class Candidat(Base):
    __tablename__ = "candidat"
    id = Column(Integer, primary_key=True)
    candidat_name = Column(String)
    parti = relationship("CandidatParti", back_populates="candidat")

class CandidatParti(Base):
    __tablename__ = "candidat_parti"
    id = Column(Integer, primary_key=True)
    courant = Column(String)
    candidat_id = Column(Integer, ForeignKey('candidat.id'))
    parti_id = Column(Integer, ForeignKey('parti.id'))
    candidat = relationship("Candidat")
    parti = relationship("Parti")

class UrneVote(Base):
    __tablename__ = "urne_vote"
    id = Column(Integer, primary_key=True, autoincrement=True)
    circonscription = Column(Integer)
    region_id = Column(Integer, ForeignKey('region.department_code'))
    annee = Column(String)
    final_round = Column(Boolean, default=False)
    is_legis = Column(Boolean, default=False)

class ResultatCondidatParti(Base):
    __tablename__ = "resultat_candidat"
    id = Column(Integer, primary_key=True)
    urne_vote_id = Column(Integer, ForeignKey('urne_vote.id'), index=True)  
    candidat_parti = Column(Integer, ForeignKey('candidat_parti.id'), index=True)  
    value = Column(Integer, default=0)

class ResultatMetaInfo(Base):
    __tablename__ = "resultat_metainfo"
    id = Column(Integer, primary_key=True)
    urne_vote_id = Column(Integer, ForeignKey('urne_vote.id'))  
    inscripts = Column(Integer, default=0)
    votants = Column(Integer, default=0)
    nullparts = Column(Integer, default=0)
    exprimes = Column(Integer, default=0)
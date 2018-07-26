import uuid
import ckan.model.meta as meta
from ckan.model.package import Package
from ckan.model.meta import mapper
from ckan.model.domain_object import DomainObject

from sqlalchemy import Table, Column, MetaData, ForeignKey, types
#from sqlalchemy.orm import mapper, relationship
from sqlalchemy.orm import relationship, relation
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model
import ckan.model.types as ckan_types
from ckan.lib.base import *

log = __import__('logging').getLogger(__name__)

Base = declarative_base()
metadata = MetaData()


def make_uuid():
    return unicode(uuid.uuid4())


class Basket(Base):
    """
    Contains the detail about a specific basket which will contain BasketElements
    """
    __tablename__ = 'basket'
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    user_id = Column('user_id', types.UnicodeText)
    children = relationship("BasketAssociation")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get(cls, basket_id):
        q = model.Session.query(Basket).filter(Basket.name == basket_id)
        obj = q.first()
        if not obj:
            q = model.Session.query(Basket).filter(Basket.id == basket_id)
            obj = q.first()
        return obj

    def as_dict(self, with_terms=False):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'children': self.children,
        }


class BasketAssociation(Base):
    '''
    A many-many relationship between baskets and packages
    '''
    __tablename__ = 'basket_association'
    basket_id = Column(types.UnicodeText, ForeignKey(Basket.id), primary_key=True)
    package_id = Column(types.UnicodeText, ForeignKey(Package.id), primary_key=True)
    child = relationship(Package)


def init_tables():
    Base.metadata.create_all(model.meta.engine)


def remove_tables():
    Basket.__table__.drop(model.meta.engine, checkfirst=False)

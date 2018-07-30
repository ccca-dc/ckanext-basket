import uuid
import ckan.model.meta as meta
from ckan.model.package import Package
from ckan.model.domain_object import DomainObject

import vdm.sqlalchemy
from sqlalchemy import Table, Column, MetaData, ForeignKey, types
#from sqlalchemy.orm import mapper, relationship
from sqlalchemy.orm import relationship, relation
from sqlalchemy.ext.declarative import declarative_base

import ckan.model as model
import ckan.model.domain_object as domain_object
import ckan.model.types as ckan_types
from ckan.lib.base import *

log = __import__('logging').getLogger(__name__)

Base = declarative_base()
metadata = MetaData()


def make_uuid():
    return unicode(uuid.uuid4())


class Basket(Base,
            domain_object.DomainObject):
    """
    Contains the detail about a specific basket which will contain BasketElements
    """
    __tablename__ = 'basket'
    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    name = Column('name', types.UnicodeText)
    user_id = Column('user_id', types.UnicodeText)
    element_type = Column(types.UnicodeText, default=u"package")
    packages = relationship("BasketAssociation")

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def get(cls, basket_id):
        if not basket_id:
            return None

        basket = meta.Session.query(cls).get(basket_id)

        return basket

    def as_dict(self, with_terms=False):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'element_type': self.element_type,
            'packages': [pkg.package_id for pkg in self.packages],
        }

    # @property
    # def packages_list(self):
    #     return [package for package in self.packages]

class BasketAssociation(Base,
                        domain_object.DomainObject):
    '''
    A many-many relationship between baskets and packages
    '''
    __tablename__ = 'basket_association'
    basket_id = Column(types.UnicodeText, ForeignKey(Basket.id), primary_key=True)
    package_id = Column(types.UnicodeText, ForeignKey(Package.id), primary_key=True)
    package = relationship(Package)
    # TODO change child to element

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    # def as_dict(self, with_terms=False):
    #     return {
    #         'basket_id': self.basket_id,
    #         'package_id': self.package_id
    #     }


def init_tables():
    Base.metadata.create_all(model.meta.engine)


def remove_tables():
    Basket.__table__.drop(model.meta.engine, checkfirst=False)
    BasketAssociation.__table__.drop(model.meta.engine, checkfirst=False)

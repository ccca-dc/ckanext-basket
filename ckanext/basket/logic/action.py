# -*- coding: utf-8 -*-

import ckan.plugins.toolkit as tk
import ckan.logic
import ckan.lib.dictization as d
import ckan.authz as authz
import ckan.lib.dictization.model_dictize as model_dictize
from ckanext.basket.models import Basket, BasketAssociation

from logging import getLogger

log = getLogger(__name__)

_get_or_bust = ckan.logic.get_or_bust
_get_action = ckan.logic.get_action


@ckan.logic.side_effect_free
def basket_create(context, data_dict):
    """Create a new basket

    :param user_id: The id of the user to create the basket for (only admin)
    :type user_id: string
    :param element_type: The type of the basket elements (e.g. package, resource, subset) (optional)
    :type element_type: string
    :returns:
    """
    tk.check_access('basket_create', context, data_dict)
    model = context['model']
    user = context['user']

    user_dct = tk.get_action("user_show")(context,{"id": user})

    # Default element_type
    if 'element_type' not in data_dict:
        data_dict['element_type'] = "package"

    # Sysadmins are allowed to pass user_id
    if 'user_id' not in data_dict or not user.get("sysadmin"):
        data_dict['user_id'] = user_dct.get('id')

    basket = d.table_dict_save(data_dict, Basket, context)

    if not context.get('defer_commit'):
        model.repo.commit()

    return basket.as_dict()


@ckan.logic.side_effect_free
def basket_purge(context, data_dict):
    """Purge a basket

    :param id: The id of the basket
    :type id: string
    :returns:
    """
    tk.check_access('basket_owner_only', context, data_dict)
    model = context['model']
    id = _get_or_bust(data_dict, 'id')

    basket = Basket.get(id)

    if basket is None:
        raise tk.ObjectNotFound('Basket was not found')

    basket_associations = model.Session.query(BasketAssociation) \
                   .filter(BasketAssociation.basket_id == id)
    if basket_associations.count() > 0:
        for ba in basket_associations.all():
            ba.purge()

    basket.purge()

    model.repo.commit()


@ckan.logic.side_effect_free
def basket_list(context, data_dict):
    """List all baskets for user

    :param user_id: The id of the user for whom to list the baskets (only admin)
    :type user_id: string
    :returns:
    """
    tk.check_access('basket_owner_only', context, data_dict)
    model = context['model']
    user = context['user']

    user_id = data_dict.get('user_id', authz.get_user_id_for_username(user, allow_none=True))
    if not user_id:
        return []

    if data_dict.get('user_id'):
        user = model.User.get(user_id)

        if user is None:
            raise tk.ObjectNotFound('User was not found')

        user_id = user.id

    q = model.Session.query(Basket).filter(Basket.user_id == user_id)

    return [d.table_dictize(basket, context) for basket in q.all()]


@ckan.logic.side_effect_free
def basket_show(context, data_dict):
    """Show basket

    :param id: The id of the basket
    :type id: string
    :param include_elements: default False (optional)
    :type include_elements: boolean
    :returns:
    """
    tk.check_access('basket_owner_only', context, data_dict)
    model = context['model']
    context['session'] = model.Session

    basket_id = _get_or_bust(data_dict, 'id')

    basket = Basket.get(basket_id)

    if basket is None:
        raise tk.ObjectNotFound('Basket was not found')

    return basket.as_dict()


@ckan.logic.side_effect_free
def basket_element_list(context, data_dict):
    """List all elements in basket

    :param id: The id of the package
    :type id: string
    :returns:
    """
    tk.check_access('basket_owner_only', context, data_dict)
    model = context['model']

    id = _get_or_bust(data_dict, 'id')

    q = model.Session.query(BasketAssociation, model.Package) \
        .filter(BasketAssociation.basket_id == id) \
        .join(model.Package)

    pkgs = []
    for basket_association, package in q.all():
        pkgs.append(model_dictize.package_dictize(package, context))

    if not pkgs:
        return []

    return pkgs


@ckan.logic.side_effect_free
def basket_element_add(context, data_dict):
    """Add an element to a basket

    :param basket_id: The id of the basket
    :type basket_id: string
    :param package_id: The id of the package
    :type package_id: string
    :returns:
    """
    tk.check_access('basket_owner_only', context, data_dict)
    model = context['model']
    user = context['user']

    basket_id, package_id = _get_or_bust(data_dict, ['basket_id', 'package_id'])

    basket = Basket.get(basket_id)

    if basket is None:
        raise tk.ObjectNotFound('Basket was not found.')

    package = model.Package.get(package_id)

    if package is None:
        raise tk.ObjectNotFound('Package was not found.')

    data_dict['package_id'] = package.id

    basket_association = d.table_dict_save(data_dict, BasketAssociation, context)

    if not context.get('defer_commit'):
        model.repo.commit()

    return basket_association.as_dict()


@ckan.logic.side_effect_free
def basket_element_remove(context, data_dict):
    """Remove an element from a basket

    :param basket_id: The id of the basket
    :type basket_id: string
    :param package_id: The id of the package
    :type package_id: string
    :returns:
    """
    tk.check_access('basket_owner_only', context, data_dict)
    model = context['model']

    basket_id, package_id = _get_or_bust(data_dict, ['basket_id', 'package_id'])

    basket = Basket.get(basket_id)
    if not basket:
        raise tk.ObjectNotFound('Basket was not found.')

    pkg = model.Package.get(package_id)
    if not pkg:
        raise tk.ObjectNotFound('Package was not found.')

    basket_association = model.Session.query(BasketAssociation).\
                        filter(BasketAssociation.basket_id == basket.id).\
                        filter(BasketAssociation.package_id == pkg.id).first()
    if basket_association:
        # rev = model.repo.new_revision()
        # rev.author = context.get('user')
        # rev.message = _(u'REST API: Delete Member: %s') % obj_id
        basket_association.delete()
        model.repo.commit()

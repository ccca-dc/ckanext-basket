# -*- coding: utf-8 -*-

import ckan.plugins.toolkit as tk
import ckan.logic
import ckan.lib.dictization as d
from ckanext.basket.models import Basket, BasketAssociation

from logging import getLogger

log = getLogger(__name__)

NotFound = ckan.logic.NotFound
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
    model = context['model']
    user = context['user']

    if 'element_type' not in data_dict:
        data_dict['element_type'] = "package"

    # TODO: only sysadmin
    if 'user_id' not in data_dict:
        data_dict['user_id'] = context['auth_user_obj'].id

    # TODO auth.py
    #_check_access('basket_create', context, data_dict)

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
    model = context['model']
    id = _get_or_bust(data_dict, 'id')

    basket = Basket.get(id)

    if basket is None:
        raise NotFound('Basket was not found')

    # _check_access('basket_purge',context, data_dict)

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

    :param user_id: The id of the user to create the basket for (optional)
    :type user_id: string
    :returns:
    """
    pass


@ckan.logic.side_effect_free
def basket_show(context, data_dict):
    """Show basket

    :param id: The id of the basket
    :type id: string
    :param include_elements: default False (optional)
    :type include_elements: boolean
    :returns:
    """
    model = context['model']
    context['session'] = model.Session
    basket_id = data_dict.get("id")
    #import ipdb; ipdb.set_trace()
    basket = Basket.get(basket_id)

    if basket is None:
        raise tk.ObjectNotFound


    # _check_access('package_show', context, data_dict)

    return basket.as_dict()


@ckan.logic.side_effect_free
def basket_element_list(context, data_dict):
    """List all elements in basket

    :param id: The id of the package
    :type id: string
    :returns:
    """
    pass


@ckan.logic.side_effect_free
def basket_element_add(context, data_dict):
    """Add an element to a basket

    :param basket_id: The id of the basket
    :type basket_id: string
    :param element_id: The id of the element
    :type element_id: string
    :returns:
    """

    model = context['model']
    user = context['user']

    # TODO auth.py
    #_check_access('basket_element_add', context, data_dict)

    basket_association = d.table_dict_save(data_dict, BasketAssociation, context)

    if not context.get('defer_commit'):
        model.repo.commit()

    return basket_association.as_dict()


@ckan.logic.side_effect_free
def basket_element_remove(context, data_dict):
    """Remove an element from a basket

    :param basket_id: The id of the basket
    :type basket_id: string
    :param element_id: The id of the element
    :type element_id: string
    :returns:
    """
    pass

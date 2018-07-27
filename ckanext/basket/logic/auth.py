import ckan.plugins.toolkit as tk

from ckan.common import _

from ckanext.basket.models import Basket, BasketAssociation

@tk.auth_disallow_anonymous_access
def basket_create(context, data_dict):
    """
    Can the user create a basket. This is only available for
    registered users.

    There is a shortcut where this will not be called for sysadmins
    """
    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_purge(context, data_dict):
    """
    Can the user purge a basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_list(context, data_dict):
    """
    Can the user list a basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    user = context['user']
    user_dct = tk.get_action("user_show")(context,{"id": user})

    # Only Sysadmins are allowed to pass user_id
    if data_dict.get('user_id') and not user_dct.get("sysadmin"):
        return {'success': False,
                'msg': _('User %s not authorized to list baskets') %
                        (str(user))}

    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_show(context, data_dict):
    """
    Can the user show a basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_element_list(context, data_dict):
    """
    Can the user list the elements from a basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_element_add(context, data_dict):
    """
    Can the user add an element to a basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_element_remove(context, data_dict):
    """
    Can the user add an element to a basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    return {'success': True}

@tk.auth_disallow_anonymous_access
def basket_owner_only(context, data_dict):
    """
    Can the user work with basket. This is only available for
    registered users and only for his baskets.

    There is a shortcut where this will not be called for sysadmins
    """
    model = context['model']
    user = context.get('user')

    user_dct = tk.get_action("user_show")(context,{"id": user})
    id = tk.get_or_bust(data_dict, 'id')

    basket = Basket.get(id)

    if basket is None:
        raise tk.ObjectNotFound('Basket was not found')

    if basket.user_id not in user_dct.get("id"):
        return {'success': False,
                'msg': _('User %s not authorized to call action in basket %s') %
                        (str(user), str(basket.id))}

    return {'success': True}

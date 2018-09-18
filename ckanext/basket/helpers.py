import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.model as model
from ckan.common import config


def basket_list_for_pkg(user, package_id):
    # returns all available baskets for package where package has not yet been added
    baskets = tk.get_action('basket_list')({}, {'user_id': user})

    filtered_baskets = list()

    if package_id is not None:
        for basket in baskets:
            if package_id not in basket['packages']:
                filtered_baskets.append(basket)
    else:
        return baskets

    return filtered_baskets


def basket_list(user):
    baskets = tk.get_action('basket_list')({}, {'user_id': user})
    return baskets


def get_basket_config():
    return config.get('ckanext.basket.max_number_of_pkgs_to_add_to_basket', 400)

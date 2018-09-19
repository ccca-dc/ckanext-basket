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


def basket_rsc_for_pkgs(packages_list):
    # returns all downloadable resources for a list of package_ids
    resources_list = []

    for pkg_dct in packages_list:
        # pkg_dct = tk.get_action("package_show")(context,{"id": pkg_id})
        for res in pkg_dct.get('resources', []):
            if res.get("url_type") == "upload":
                resources_list.append(res.get("url"))

    return resources_list

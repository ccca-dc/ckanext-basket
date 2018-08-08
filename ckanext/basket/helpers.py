import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.model as model


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

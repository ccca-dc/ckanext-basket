import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.model as model

def basket_list(user):
    baskets = tk.get_action('basket_list')({}, {'user_id': user})
    return baskets


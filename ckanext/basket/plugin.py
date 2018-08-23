import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.basket import helpers


class BasketPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions, inherit=True)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'basket')

    # IAuthFunctions
    def get_actions(self):
        import ckanext.basket.logic.action as action
        actions = {'basket_create': action.basket_create,
                    'basket_update': action.basket_update,
                    'basket_element_add': action.basket_element_add,
                    'basket_purge': action.basket_purge,
                    'basket_list': action.basket_list,
                    'basket_show': action.basket_show,
                    'basket_element_list': action.basket_element_list,
                    'basket_element_remove': action.basket_element_remove}
        return actions

    # IAuthFunctions
    def get_auth_functions(self):
        import ckanext.basket.logic.auth as auth
        return {
            'basket_create': auth.basket_create,
            'basket_update': auth.basket_update,
            'basket_purge': auth.basket_purge,
            'basket_list': auth.basket_list,
            'basket_show': auth.basket_show,
            'basket_element_list': auth.basket_element_list,
            'basket_element_remove': auth.basket_element_remove,
            'basket_owner_only': auth.basket_owner_only
        }

    # IRoutes
    def before_map(self, map):
        # About pages
        map.connect('basket_index', '/basket',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='index')
        map.connect('basket_new', '/basket/new',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='new')
        map.connect('basket_read', '/basket/{id}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='read')
        map.connect('basket_edit', '/basket/edit/{id}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='edit')
        map.connect('basket_delete', '/basket/delete/{id}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='delete')
        map.connect('add_package_to_basket', '/basket/add_package/{basket_id}/{package_id}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='add_package_to_basket')
        map.connect('add_packages_to_basket', '/basket/add_packages/{basket_id}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='add_packages_to_basket')
        map.connect('add_user_packages_to_basket', '/basket/add_user_packages/{basket_id}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='add_user_packages_to_basket')
        map.connect('add_org_packages_to_basket', '/basket/add_org_packages/{basket_id}/{org_name}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='add_org_packages_to_basket')
        map.connect('add_group_packages_to_basket', '/basket/add_group_packages/{basket_id}/{group_name}',
                    controller='ckanext.basket.controllers.basket:BasketController',
                    action='add_group_packages_to_basket')

        return map

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'basket_list_for_pkg': helpers.basket_list_for_pkg
            }

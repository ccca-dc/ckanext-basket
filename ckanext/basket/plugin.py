import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit


class BasketPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions, inherit=True)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'basket')

    # IAuthFunctions
    def get_actions(self):
        import ckanext.basket.logic.action as action
        actions = {'basket_create': action.basket_create,
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
            'basket_purge': auth.basket_purge,
            'basket_list': auth.basket_list,
            'basket_show': auth.basket_show,
            'basket_element_list': auth.basket_element_list,
            'basket_element_remove': auth.basket_element_remove,
            'basket_owner_only': auth.basket_owner_only
        }

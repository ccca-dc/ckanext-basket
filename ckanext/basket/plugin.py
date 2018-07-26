import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.basket.action as action


class BasketPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'basket')

    def get_actions(self):
        actions = {'basket_create': action.basket_create,
                    'basket_element_add': action.basket_element_add}
        return actions

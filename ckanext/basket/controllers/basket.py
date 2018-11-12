# encoding: utf-8

import logging
import datetime
from urllib import urlencode

from pylons.i18n import get_lang

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckanext.ccca.helpers as ccca_helpers
import ckan.lib.maintain as maintain
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.lib.search as search
import ckan.model as model
import ckan.authz as authz
import ckan.lib.plugins
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ast
from ckan.common import OrderedDict, c, g, request, _, config
from paste.deploy.converters import asbool

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = base.redirect

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action
tuplize_dict = logic.tuplize_dict
clean_dict = logic.clean_dict
parse_params = logic.parse_params

lookup_group_plugin = ckan.lib.plugins.lookup_group_plugin
lookup_group_controller = ckan.lib.plugins.lookup_group_controller


class BasketController(base.BaseController):

    def index(self):

        page = h.get_page_number(request.params) or 1
        items_per_page = 21

        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'for_view': True,
                   'with_private': False}

        q = c.q = request.params.get('q', '')
        sort_by = c.sort_by_selected = request.params.get('sort')
        try:
            tk.check_access('basket_list', context, {})
        except NotAuthorized:
            abort(403, _('Not authorized to see this page'))

        # pass user info to context as needed to view private datasets of
        # orgs correctly
        if c.userobj:
            context['user_id'] = c.userobj.id
            context['user_is_admin'] = c.userobj.sysadmin

        try:
            data_dict_global_results = {
                'all_fields': False,
                'q': q,
                'sort': sort_by,
            }
            global_results = tk.get_action('basket_list')(
                context, data_dict_global_results)
        except ValidationError as e:
            if e.error_dict and e.error_dict.get('message'):
                msg = e.error_dict['message']
            else:
                msg = str(e)
            h.flash_error(msg)
            c.page = h.Page([], 0)
            # return render(self._index_template(group_type),
            #               extra_vars={'group_type': group_type})

        page_results = tk.get_action('basket_list')(context, {})

        c.page = h.Page(
            collection=global_results,
            page=page,
            url=h.pager_url,
            items_per_page=items_per_page,
        )

        c.page.items = page_results
        return tk.render('basket/index.html', {'title': 'Baskets'})

    def read(self, id):
        # gets called for individual basket page
        # export, clear, delete and group buttons on read page call this method

        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        data_dict = {'id': id}

        # unicode format (decoded from utf8)
        c.q = request.params.get('q', '')

        # use different form names so that ie7 can be detected

        form_names = set(["bulk_action.export",
                          "bulk_action.clear",
                          "bulk_action.delete",
                          "bulk_action.group"])
        actions_in_form = set(request.params.keys())
        actions = form_names.intersection(actions_in_form)


        # If no action (no buttons pressed) then just show the datasets
        if actions:
            #ie7 puts all buttons in form params but puts submitted one twice
            for key, value in dict(request.params.dict_of_lists()).items():
                if len(value) == 2:
                    action = key.split('.')[-1]
                    break
            else:
                #normal good browser form submission
                action = actions.pop().split('.')[-1]

            # process the action first find the datasets to perform the action on.
            # they are prefixed by dataset_ in the form data
            datasets = []
            for param in request.params:
                if param.startswith('dataset_'):
                    datasets.append(param[8:])

            if len(datasets) > 0:
                if action == 'group':
                    for dataset in datasets:
                        member_dict = dict()
                        member_dict['id'] = request.params.get('bulk_action.group')
                        member_dict['object'] = dataset
                        member_dict['object_type'] = 'package'
                        member_dict['capacity'] = 'public'
                        tk.get_action('member_create')(context, member_dict)
                    h.flash_notice(_('Packages have been added to Group %s.') % (member_dict['id']))

                else:
                    action_functions = {
                        'export': 'basket_export',
                        'clear': 'basket_clear',
                        'delete': 'basket_element_remove',
                    }


                    data_dict_action = {'packages': datasets, 'basket_id': data_dict['id']}

                    # TODO undo changes if autocreation of homedirectory works
                    # Flash messages
                    if "delete" in action:
                        try:
                            get_action(action_functions[action])(context, data_dict_action)
                        except NotAuthorized:
                            abort(403, _('Not authorized to perform bulk update'))

                        h.flash_notice(_('Packages have been deleted from basket.'))
                    elif "clear" in action:
                        h.flash_notice(_('FEATURE NOT YET IMPLEMENTED: Packages have been cleared from home directory.'))
                    elif "export" in action:
                        h.flash_notice(_('FEATURE NOT YET IMPLEMENTED: Packages have been exported to home directory.'))

                    # TODO uncomment if autocreation of homedirectory works
                    # # Flash messages
                    # if "delete" in action:
                    #     h.flash_notice(_('Packages have been deleted from basket.'))
                    # elif "clear" in action:
                    #     h.flash_notice(_('Packages have been cleared from home directory.'))
                    # elif "export" in action:
                    #     h.flash_notice(_('Packages have been exported to home directory.'))
        try:
            # Do not query for the group datasets when dictizing, as they will
            # be ignored and get requested on the controller anyway

            # get basket and packages info and all groups, to which the user can add datasets
            c.basket_dict = tk.get_action('basket_show')(context, data_dict)
            c.packages = tk.get_action('basket_element_list')(context, data_dict)
            users_groups = get_action('group_list_authz')(context, {})

            # additional group_list is needed to get type of group
            dict_group_list = dict()
            dict_group_list['all_fields'] = True
            dict_group_list['include_extras'] = True
            dict_group_list['groups'] = [group['name'] for group in users_groups]
            c.groups = get_action('group_list')(context, dict_group_list)

        except (NotFound, NotAuthorized):
            abort(404, _('Basket not found'))

        return tk.render('basket/read.html', {'title': 'Basket'})

    def new(self, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'save': 'save' in request.params}

        try:
            tk.check_access('basket_create', context)
        except NotAuthorized:
            abort(403, _('Unauthorized to create a basket'))

        if context['save'] and not data and request.method == 'POST':
            return self._save_new(context)

        data = data or {}

        errors = errors or {}
        error_summary = error_summary or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'new'}

        return tk.render('basket/new.html', vars)

    def _save_new(self, context):
        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.params))))
            context['message'] = data_dict.get('log_message', '')
            data_dict['user_id'] = c.user
            basket = tk.get_action('basket_create')(context, data_dict)

            # Redirect to the new basket
            url = h.url_for(controller='ckanext.basket.controllers.basket:BasketController',
                action='read',
                id=basket['id'])
            redirect(url)

        except (NotFound, NotAuthorized), e:
            abort(404, _('Basket not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data_dict, errors, error_summary)

    def edit(self, id, data=None, errors=None, error_summary=None):
        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'save': 'save' in request.params,
                   'for_edit': True
                   }
        data_dict = {'id': id}

        if context['save'] and not data and request.method == 'POST':
            return self._save_edit(id, context)

        try:
            old_data = tk.get_action('basket_show')(context, data_dict)
            c.basketname = old_data.get('name')
            data = data or old_data
        except (NotFound, NotAuthorized):
            abort(404, _('Basket not found'))

        basket = context.get("basket")
        c.basket = basket
        c.basket_dict = tk.get_action('basket_show')(context, data_dict)

        try:
            tk.check_access('basket_update', context)
        except NotAuthorized:
            abort(403, _('User %r not authorized to edit %s') % (c.user, id))

        errors = errors or {}
        vars = {'data': data, 'errors': errors,
                'error_summary': error_summary, 'action': 'edit'}

        return tk.render('basket/edit.html', vars)

    def _save_edit(self, id, context):
        try:
            data_dict = clean_dict(dict_fns.unflatten(
                tuplize_dict(parse_params(request.params))))

            data_dict['id'] = id
            context['allow_partial_update'] = True
            basket = tk.get_action('basket_update')(context, data_dict)

            url = h.url_for(controller='ckanext.basket.controllers.basket:BasketController',
                action='read',
                id=basket['id'])
            redirect(url)
        except (NotFound, NotAuthorized), e:
            abort(404, _('Basket not found'))
        except dict_fns.DataError:
            abort(400, _(u'Integrity Error'))
        except ValidationError, e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.edit(id, data_dict, errors, error_summary)

    def delete(self, id):
        if 'cancel' in request.params:
            self._redirect_to_this_controller(action='edit', id=id)

        context = {'model': model, 'session': model.Session,
                   'user': c.user}

        try:
            tk.check_access('basket_purge', context, {'id': id})
        except NotAuthorized:
            abort(403, _('Unauthorized to delete basket %s') % '')

        try:
            if request.method == 'POST':
                tk.get_action('basket_purge')(context, {'id': id})
                h.flash_notice(_('Basket has been deleted.'))
                url = h.url_for(controller='ckanext.basket.controllers.basket:BasketController',
                    action='index')
                redirect(url)
            c.group_dict = tk.get_action('basket_show')(context, {'id': id})
        except NotAuthorized:
            abort(403, _('Unauthorized to delete basket %s') % '')
        except NotFound:
            abort(404, _('Basket not found'))
        return tk.render('basket/confirm_delete.html', vars)

    def add_package_to_basket(self, basket_id, package_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user}

        try:
            tk.check_access('basket_owner_only', context, {'id': basket_id})
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))

        try:
            tk.get_action('basket_element_add')(context, {'basket_id': basket_id, 'package_id': package_id})
            h.flash_notice(_('Package has been added to Basket.'))
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))
        except NotFound:
            abort(404, _('Package not found'))

        redirect_url = request.params.get('redirect_url', '/dataset')
        return h.redirect_to(str(redirect_url))

    def add_packages_to_basket(self, basket_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user}

        try:
            tk.check_access('basket_owner_only', context, {'id': basket_id})
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))

        request_params = request.params['request_params']
        fields_grouped = request.params['fields_grouped']

        request_params = ast.literal_eval(request_params)
        q = request_params.get('q', '')
        fields_grouped = ast.literal_eval(fields_grouped)

        # adding search extras (bbox, date)
        search_extras = {}
        for (param, value) in request_params.items():
            if param not in ['q', 'page', 'sort'] \
                    and len(value) and not param.startswith('_') \
                    and param.startswith('ext_'):
                    search_extras[param] = value

        packages = self._get_packages_for_basket(context, q, '', fields_grouped, search_extras)
        self._add_packages_to_basket(context, basket_id, packages)

        url = h.url_for('/dataset')
        redirect(url)

    def add_user_packages_to_basket(self, basket_id):
        packages = request.params['creator_packages'].split(",")

        context = {'model': model, 'session': model.Session,
                   'user': c.user}

        try:
            tk.check_access('basket_owner_only', context, {'id': basket_id})
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))

        packages.extend(pkg['id'] for pkg in ccca_helpers.ccca_get_datasets_by_role('author', c.user))
        packages.extend(pkg['id'] for pkg in ccca_helpers.ccca_get_datasets_by_role('maintainer', c.user))

        self._add_packages_to_basket(context, basket_id, list(set(packages)))

        url = h.url_for(controller='user',
            action='read',
            id=c.user)
        redirect(url)

    def add_org_packages_to_basket(self, basket_id, org_name):
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        try:
            tk.check_access('basket_owner_only', context, {'id': basket_id})
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))

        # adding search params
        fields_grouped = request.params['fields_grouped']
        fields_grouped = ast.literal_eval(fields_grouped)

        fq = ' %s:"%s"' % ('organization', org_name)
        q = request.params.get('q', '')

        packages = self._get_packages_for_basket(context, q, fq, fields_grouped, {})
        self._add_packages_to_basket(context, basket_id, list(set(packages)))

        url = h.url_for(controller='organization',
            action='read',
            id=org_name)
        redirect(url)

    def add_group_packages_to_basket(self, basket_id, group_name):
        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        try:
            tk.check_access('basket_owner_only', context, {'id': basket_id})
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))

        # adding search params
        fields_grouped = request.params['fields_grouped']
        fields_grouped = ast.literal_eval(fields_grouped)

        fq = ' %s:"%s"' % ('groups', group_name)
        q = request.params.get('q', '')

        packages = self._get_packages_for_basket(context, q, fq, fields_grouped, {})
        self._add_packages_to_basket(context, basket_id, list(set(packages)))

        url = h.url_for(controller='group',
            action='read',
            id=group_name)
        redirect(url)

    def _get_packages_for_basket(self, context, q, fq, fields_grouped, search_extras):
        for key, values in fields_grouped.iteritems():
            for v in values:
                fq += ' %s:"%s"' % (key, v)

        data_dict = {
                'q': q,
                'fq': fq,
                'rows': 1000,
                'extras': search_extras,
                'include_private': asbool(config.get(
                    'ckan.search.default_include_private', True)),
                }

        query = tk.get_action('package_search')(context, data_dict)
        packages = [pkg['id'] for pkg in query['results']]

        return packages

    def _add_packages_to_basket(self, context, basket_id, packages):
        try:
            basket = tk.get_action('basket_show')(context, {'id': basket_id})
            basket_associations = tk.get_action('basket_element_add')(context, {'basket_id': basket['id'], 'packages': packages})
            if len(basket_associations) == 1:
                h.flash_notice(_('1 Package has been added to Basket "%s".') % (basket['name']))
            elif len(basket_associations) > 0:
                h.flash_notice(_('%s Packages have been added to Basket "%s".') % (len(basket_associations), basket['name']))
            else:
                h.flash_notice(_('No new Package has been added to Basket "%s".') % (basket['name']))
        except NotAuthorized:
            abort(403, _('Unauthorized to add package to basket'))
        except NotFound:
            abort(404, _('Package not found'))

    def remove_package_from_basket(self, basket_id, package_id):
        context = {'model': model, 'session': model.Session,
                   'user': c.user}

        try:
            tk.check_access('basket_owner_only', context, {'id': basket_id})
        except NotAuthorized:
            abort(403, _('Unauthorized to remove package from basket'))

        try:
            tk.get_action('basket_element_remove')(context, {'basket_id': basket_id, 'package_id': package_id})
            h.flash_notice(_('Package has been removed from Basket.'))
        except NotAuthorized:
            abort(403, _('Unauthorized to remove package from basket'))
        except NotFound:
            abort(404, _('Package not found'))

        redirect_url = request.params.get('redirect_url', '/dataset')
        return h.redirect_to(str(redirect_url))

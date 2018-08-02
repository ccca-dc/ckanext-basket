# encoding: utf-8

import logging
import datetime
from urllib import urlencode

from pylons.i18n import get_lang

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.maintain as maintain
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.lib.search as search
import ckan.model as model
import ckan.authz as authz
import ckan.lib.plugins
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
from ckan.common import OrderedDict, c, g, request, _

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
        # import ipdb; ipdb.set_trace()
        return tk.render('basket/index.html', {'title': 'Baskets'})

    def read(self, id, limit=20):

        context = {'model': model, 'session': model.Session,
                   'user': c.user}
        data_dict = {'id': id}

        # unicode format (decoded from utf8)
        c.q = request.params.get('q', '')

        try:
            # Do not query for the group datasets when dictizing, as they will
            # be ignored and get requested on the controller anyway
            # data_dict['include_datasets'] = False
            c.basket_dict = tk.get_action('basket_show')(context, data_dict)
            c.packages = tk.get_action('basket_element_list')(context, data_dict)
            # c.group = context['group']
        except (NotFound, NotAuthorized):
            abort(404, _('Basket not found'))

        # self._read(id, limit, group_type)
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

        # self._setup_template_variables(context, data, group_type=group_type)
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

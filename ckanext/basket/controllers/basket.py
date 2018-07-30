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
from ckan.common import OrderedDict, c, g, request, _

log = logging.getLogger(__name__)

render = base.render
abort = base.abort

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
            # group_type = self._guess_group_type()

            page = h.get_page_number(request.params) or 1
            items_per_page = 21

            context = {'model': model, 'session': model.Session,
                       'user': c.user, 'for_view': True,
                       'with_private': False}

            q = c.q = request.params.get('q', '')
            sort_by = c.sort_by_selected = request.params.get('sort')
            try:
                plugins.toolkit.check_access('basket_list', context, {})
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
                global_results = plugins.toolkit.get_action('basket_list')(
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

            # data_dict_page_results = {
            #     'all_fields': True,
            #     'q': q,
            #     'sort': sort_by,
            #     'limit': items_per_page,
            #     'offset': items_per_page * (page - 1),
            # }
            page_results = plugins.toolkit.get_action('basket_list')(context,
                                                      {})

            c.page = h.Page(
                collection=global_results,
                page=page,
                url=h.pager_url,
                items_per_page=items_per_page,
            )

            c.page.items = page_results
            return plugins.toolkit.render('basket/index.html', {'title': 'Baskets'})

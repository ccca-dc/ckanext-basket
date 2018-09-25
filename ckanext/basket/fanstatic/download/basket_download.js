ckan.module('basket_download', function ($) {
  return {
      /* options object can be extended using data-module-* attributes */
      options: {
          rscs_list: '',
      }, //options

      initialize: function () {
        var self = this;
        var options = this.options;
        $.proxyAll(this, /_on/);
        // Uncheck all checkboxes (table-selected class missing after reload)
        $(':checkbox:checked').removeAttr('checked');
        var table = $('#tab-basket').DataTable({"ordering": false});
        // Add click event
        document.getElementById('js_action.download').addEventListener('click', function(e){
            self._DownloadResources();
        });
      },

      _DownloadResources: function() {
          // Reload table (maybe checkboxes changed)
          var table = $('#tab-basket').DataTable();
          // Get seleted rows
          var sel_pkg_ids = $.map(table.rows('.table-selected').ids(), function (item) {
              return item;
          });

          // Filter resources for selected packages
          var results = this.options.rscs_list.filter(
              function(e_rsc) {
                  let in_list = false;
                  this.forEach(e_pkg => {
                      in_list = in_list || e_rsc.includes(e_pkg);
                  });
                  return in_list;
              },
              sel_pkg_ids
          );

          // Open download dialogues for selected resources
          var link = document.createElement('a');

          link.setAttribute('download', null);
          link.style.display = 'none';
          document.body.appendChild(link);

          for (var i = 0; i < results.length; i++) {
              link.setAttribute('href', results[i]);
              link.click();
          }
          document.body.removeChild(link);
      }
  };
});

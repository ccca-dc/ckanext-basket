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
        // Add click event
        $(':checkbox:checked').prop('checked',false);
        var table = $('#tab-basket').DataTable({"ordering": false});
        document.getElementById('js_action.download').addEventListener('click', function(e){
            self._DownloadResources();
        });
      },

      _DownloadResources: function() {
          var table = $('#tab-basket').DataTable();
          var sel_pkg_ids = $.map(table.rows('.table-selected').ids(), function (item) {
              return item;
          });

          var results = this.options.rscs_list.filter(
              function(e) {
                  return e.indexOf(this) > -1;
              },
              sel_pkg_ids
          );

          console.log(sel_pkg_ids);
          console.log(results);

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

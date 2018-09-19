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
        document.getElementById('js_action.download').addEventListener('click', function(e){
            self._DownloadResources();
        });
      },

      _DownloadResources: function() {
        var link = document.createElement('a');

        link.setAttribute('download', null);
        link.style.display = 'none';

        document.body.appendChild(link);

        for (var i = 0; i < this.options.rscs_list.length; i++) {
            link.setAttribute('href', this.options.rscs_list[i]);
            link.click();
        }
        document.body.removeChild(link);
      }
  };
});

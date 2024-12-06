(function(define) {
  'use strict';

  define(['backbone'], function(Backbone) {
    return Backbone.Model.extend({
      idAttribute: 'id',
      defaults: {
        course_id: '',
        usage_id: '',
        display_name: '',
        path: [],
        created: ''
      },

      blockUrl: function() {
        var path = this.get('path');
        var url = '/courses/' + this.get('course_id') + '/jump_to/' + this.get('usage_id');
        var params = new URLSearchParams();
        var usage_id = this.get('usage_id');
        // Confirm that current usage_id does not correspond to current unit
        // path contains an array of parent blocks to the bookmarked block.
        // Units only have two parents i.e. section and subsections.
        // Below condition is only satisfied if a block lower than unit is bookmarked.
        if (path.length > 2 && usage_id !== path[path.length - 1]) {
          params.append('jumpToId', usage_id);
        }
        if (params.size > 0) {
          // Pass nested block details via query parameters for it to be passed to learning mfe
          // The learning mfe should pass it back to unit xblock via iframe url params.
          // This would allow us to scroll to the child xblock.
          url = url + '?' + params.toString();
        }
        return url;
      }
    });
  });
}(define || RequireJS.define));

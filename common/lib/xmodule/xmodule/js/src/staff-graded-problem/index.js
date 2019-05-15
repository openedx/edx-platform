(function() {
  'use strict'
  this.StaffGradedProblem = function(runtime, element, json_args) {
    var $element = $(element);
    var fileInput = $element.find('.file-input');
    fileInput.change(function(e){
      var firstFile = this.files[0];
      var self = this;
      if (firstFile == undefined) {
        return;
      }
      var formData = new FormData();
      formData.append('csrfmiddlewaretoken', json_args.csrf_token);
      formData.append('csv', firstFile);

      $element.find('.filename').html(firstFile.name);
      $element.find('.status').hide();
      $element.find('.spinner').show();
      $.ajax({
        url : json_args.import_url,
        type : 'POST',
        data : formData,
        processData: false,  // tell jQuery not to process the data
        contentType: false,  // tell jQuery not to set contentType
        success : function(data) {
          self.value = '';
          if (data.waiting) {
            setTimeout(function(){
              pollResults(json_args.id, data.result_id);
            }, 1000);
          } else {
            doneLoading(json_args.id, data);
          }
        }
      });

    });
  };

}).call(this);

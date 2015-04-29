(function (){
    function progressHandlingFunction(event){
        if(event.lengthComputable){
            var percent = parseInt(event.loaded / event.total * 100, 10);
            $('.upload').text('Uploading... ' + percent + '%');
        }
    }
    function beforeSendHandler(){
        var outputBox = $('.output-box');
        outputBox.children('.loading').text('Loading...');
        var successBox = outputBox.children('.success').find('p');
        var errorBox = outputBox.children('.error').find('p');
        successBox.html('');
        errorBox.html('');
    }
    function reloadUploader(){
        var uploadDiv = $('.upload');
        var fileUploadElement = $(document.createElement('input'));
        fileUploadElement.addClass('fileupload');
        fileUploadElement.attr({
            'name': 'lti-grades',
            'type': 'file',
            'accept': '.csv'
        });
        var selectButton = $(document.createElement('button'));
        selectButton.addClass('select-file-button');
        selectButton.text('Select a file');
        selectButton.click(function(event){event.preventDefault();});
        uploadDiv.html(fileUploadElement);
        uploadDiv.append(selectButton);
        fileUploadElement.change(updateFileField);
    }
    function completeHandler(response){
        var outputBox = $('.output-box');
        var successBox = outputBox.children('.success').find('ul');
        var errorBox = outputBox.children('.error').find('ul');
        outputBox.children('.loading').text('');
        successBox.html('');
        errorBox.html('');
        $.each(response.status.success, function (index, row){
            var li_elt = $(document.createElement('li'));
            li_elt.append(row);
            successBox.append(li_elt);
        });
        $.each(response.status.error, function (index, row){
            var li_elt = $(document.createElement('li'));
            li_elt.append(row);
            errorBox.append(li_elt);
        });
        reloadUploader();
    }
    function upload_lti(event){
        $form = $(event.target).closest('form');
        var formData = new FormData($form[0]);
        $.ajax({
            url: $form.attr('action'),  //Server script to process data
            type: 'POST',
            xhr: function() {  // Custom XMLHttpRequest
                var myXhr = $.ajaxSettings.xhr();
                if(myXhr.upload){ // Check if upload property exists
                    myXhr.upload.addEventListener('progress', progressHandlingFunction, false); // For handling the progress of the upload
                }
                return myXhr;
            },
            //Ajax events
            beforeSend: beforeSendHandler,
            success: completeHandler,
            // Form data
            data: formData,
            //Options to tell jQuery not to process data or worry about content-type.
            cache: false,
            contentType: false,
            processData: false
        });
    }
    function load_lti_endpoints(){
        function compare_endpoints(a, b){
            if (a.display_name < b.display_name) return -1;
            if (a.display_name > b.display_name) return 1;
            return 0;
        }
        $.ajax({
            url: 'lti_rest_endpoints/',
            type: 'GET',
            dataType: 'json',
            context: this,
            success: function(endpoints) {
                endpoints.sort(compare_endpoints);
                for (var i = 0; i < endpoints.length; i++){
                    var $option = $(document.createElement('option'));
                    $option.val(endpoints[i].lti_2_0_result_service_json_endpoint);
                    $option.text(endpoints[i].display_name);
                    $option.appendTo($('.endpoint-selector'));
                }
            },
            error: null
        });
    }
    function updateFileField(event){
        var $filefield = $(event.target);
        var $select_file_button = $filefield.siblings('.select-file-button');
        if ($filefield.val()){
            $filefield.css('z-index', '1');
            $select_file_button.css('z-index', '2');
            var filename = $filefield.val().replace(/^.*[\\\/]/, '');
            $select_file_button.text('Upload ' + filename)
            $select_file_button.click(upload_lti);
        }
    }
    $(function(){
        load_lti_endpoints();
        reloadUploader();
    });
})();

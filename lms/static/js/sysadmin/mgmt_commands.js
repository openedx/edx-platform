(function () {
    // If new commands are added here that modify the database, be sure to check
    // expected behavior in error cases, since the backend handles these as
    // non_atomic_requests (specifically to work with the regenerate_user command)
    var commands = [
        {
            'display_name': gettext('Whitelist a user'),
            'method': 'cert_whitelist',
            'description': gettext('Add a user to the whitelist for a course'),
            'kwargs': [
                {
                    'argument': 'add',
                    'display_name': gettext('username'),
                    'required': true,
                },
                {
                    'argument': 'course_id',
                    'display_name': gettext('course_id'),
                    'required': true,
                },
            ],
        },
        {
            'display_name': gettext('De-whitelist a user'),
            'method': 'cert_whitelist',
            'description': gettext('Remove a user from the whitelist for a course'),
            'kwargs': [
                {
                    'argument': 'del',
                    'display_name': gettext('username'),
                    'required': true,
                },
                {
                    'argument': 'course_id',
                    'display_name': gettext('course_id'),
                    'required': true,
                },
            ],
        },
        {
            'display_name': gettext('View user whitelist'),
            'method': 'cert_whitelist',
            'description': gettext('View the list of whitelisted users for a course'),
            'kwargs': [
                {
                    'argument': 'course_id',
                    'display_name': gettext('course_id'),
                    'required': true,
                },
            ],
        },
        {
            // If this command is removed from the sysadmin, the non_atomic_requests decorator can be removed
            // from the backend dispatch() method
            'display_name': gettext('Generate a single certificate'),
            'method': 'regenerate_user',
            'description': gettext('Put a request on the queue to recreate the certificate for a particular user in a particular course'),
            'kwargs': [
                {
                    'argument': 'course',
                    'display_name': gettext('course_id'),
                    'required': true,
                },
                {
                    'argument': 'username',
                    'display_name': gettext('username'),
                    'required': true,
                },
                {
                    'argument': 'grade_value',
                    'display_name': gettext('grade'),
                    'required': false,
                },
                {
                    'argument': 'designation',
                    'display_name': gettext('designation'),
                    'required': false,
                },
                {
                    'argument': 'template_file',
                    'display_name': gettext('template'),
                    'required': false,
                },
            ]
        },
        {
            'display_name': gettext('Update certificate status'),
            'method': 'update_cert_status',
            'description': gettext('Update the status of a certificate for a particular user in a particular course'),
            'kwargs': [
                {
                    'argument': 'course_id',
                    'display_name': gettext('course_id'),
                    'required': true,
                },
                {
                    'argument': 'username_or_email',
                    'display_name': gettext('username or email'),
                    'required': true,
                },
                {
                    'argument': 'status',
                    'display_name': gettext('status (defaults to `unavailable`)'),
                    'required': false,
                },
            ],
        },
    ]

    function commandChanged(e){
        var command_key = $(e.target).val();
        loadCommand(command_key);
    }

    function updateElementWithContent($element, content){
        var paragraph = $(document.createElement('p'));
        paragraph.addClass($element.attr('output-type'));
        paragraph.html(content.replace(/(?:\r\n|\r|\n)/g, '<br />'));
        $element.append(paragraph);
    }

    function submitForm(event){

        var form = $('#command-form');
        var form_data = form.clone();
        form_data.find('input:not([required])').filter(function() {
            return $(this).val() === '';
        }).remove();
        var button = $(event.target);
        button.prop('disabled',true);

        $.ajax({
            url: '/sysadmin/mgmt_commands/',
            type: 'POST',
            data: form_data.serialize(),
            dataType: 'json',
            success: function(data) {

                $errorBox = $('.mgmt-commands-body .error');
                $stdErrLogBox = $('.mgmt-commands-body .stderr');
                $stdOutLogBox = $('.mgmt-commands-body .stdout');

                $errorBox.html('<h3 class="error">Errors:</h3>');
                $stdErrLogBox.html('<h3 class="stderr">Std Error:</h3>');
                $stdOutLogBox.html('<h3 class="stdout">Std Out:</h3>');

                if (data.error != null){
                    updateElementWithContent($errorBox, data.error);
                }
                if (data.stderr != null){
                    updateElementWithContent($stdErrLogBox, data.stderr);
                }
                if (data.stdout != null){
                    updateElementWithContent($stdOutLogBox, data.stdout);
                }
                button.prop('disabled', false);
            },
            error: function(std_ajax_err) {
              console.log('Management Command failed to execute');
            },
        });
    }

    function generateInputRow(arg, type){
        var $inputRow = $(document.createElement('div'));
        $inputRow.addClass('form-actions');
        var label = $(document.createElement('label'));
        label.html(arg.display_name);
        var input = $(document.createElement('input'));

        if (arg.required){
            label.append('*');
            input.prop('required', true);
        }


        if (type == 'kwarg'){

            label.attr('for', arg.argument);
            input.attr('type', 'text');
            input.addClass('textfield-tag');
            input.attr('name', arg.argument);
            $inputRow.append(label);
            $inputRow.append(input);
        }
        else if (type == 'kwflag'){
            label.attr('for', 'kwflags');
            label.addClass('checkbox-label');
            input.attr('type', 'checkbox');
            input.attr('name', 'kwflags');
            input.val(arg.argument);
            $inputRow.append(input);
            $inputRow.append(label);
        }
        else if (type === 'arg'){
            label.attr('for', 'args');
            input.attr('type', 'text');
            input.addClass('textfield-tag');
            input.attr('name', 'args');
            $inputRow.append(label);
            $inputRow.append(input);
        }


        return $inputRow;
    }

    function loadCommand(command_key){
        var command = commands[command_key];
        // update description
        $('#command-description').text(command.description);

        // update form
        var $form_fieldset = $('#form-fieldset');
        $form_fieldset.html('');
        var legend = $(document.createElement('legend'));
        legend.html(command.display_name);
        $form_fieldset.append(legend);
        if (command.kwargs && command.kwargs.length> 0){
            $form_fieldset.append('<h4>Keyword Arguments:</h4>');
        }
        for (var key in command.kwargs){
            var kwarg = command.kwargs[key];
            var inputRow = generateInputRow(kwarg, 'kwarg');
            $form_fieldset.append(inputRow);
        }
        if (command.kwflags && command.kwflags.length > 0){
            $form_fieldset.append('<h4 class="new-section">Keyword Flags:</h4>');
        }
        for (var key in command.kwflags){
            var kwflag = command.kwflags[key];
            var inputRow = generateInputRow(kwflag, 'kwflag');
            $form_fieldset.append(inputRow);
        }
        if (command.args && command.args.length > 0){
            $form_fieldset.append('<h4 class="new-section">Arguments:<h4>');
        }
        for (var key in command.args){
            var arg = command.args[key];
            var inputRow = generateInputRow(arg, 'arg');
            $form_fieldset.append(inputRow);
        }
        var commandName = $(document.createElement('input'));
        commandName.attr({
            type: 'hidden',
            name: 'command',
        });
        commandName.val(command.method);
        $form_fieldset.append(commandName);

        var submitButton = $(document.createElement('button'));
        submitButton.addClass('execute-command-button');
        submitButton.attr('type', 'button');
        submitButton.val('execute_command');
        submitButton.html(gettext('Execute Command'));

        submitButton.click(submitForm)
        $form_fieldset.append(submitButton);

    }

    function createSelectDiv(){
        var selectDiv = $(document.createElement('div'));
        selectDiv.addClass('command-selector');
        var selectTag = $(document.createElement('select'));
        selectTag.addClass('full-width');
        selectTag.addClass('select-tag');

        for (var key in commands){
            var command = commands[key];
            var optionTag = $(document.createElement('option'));
            optionTag.html(command.display_name);
            optionTag.val(key);
            selectTag.append(optionTag);
        }
        selectTag.bind("change", commandChanged);
        selectDiv.append(selectTag);

        var descriptionParagraph = $(document.createElement('p'));
        descriptionParagraph.html('<h1>description</h1>');
        descriptionParagraph.attr('id', 'command-description');
        selectDiv.append(descriptionParagraph);

        return selectDiv;
    }

    function createFormWrapperDiv(){
        var formWrapperDiv = $(document.createElement('div'));

        var form = $(document.createElement('form'));
        form.attr('id', 'command-form');

        var formFieldset = $(document.createElement('fieldset'));
        formFieldset.attr('id', 'form-fieldset');
        formFieldset.addClass('bordered-fieldset');
        form.append(formFieldset);

        formWrapperDiv.append(form);

        return formWrapperDiv;
    }

    function createOutputConsoleDiv(){
        var outputConsoleDiv = $(document.createElement('div'));
        var outputConsoleFieldset = $(document.createElement('fieldset'));
        outputConsoleFieldset.addClass('bordered-fieldset');

        var outputConsoleLegend = $(document.createElement('legend'));
        outputConsoleLegend.text('Output Console');

        outputConsoleFieldset.append(outputConsoleLegend);
        var errorDiv = $(document.createElement('div'));
        errorDiv.addClass('error');
        errorDiv.attr('output-type', 'error');
        var stdErrDiv = $(document.createElement('div'));
        stdErrDiv.addClass('stderr new-section');
        stdErrDiv.attr('output-type', 'stderr');
        var stdOutDiv = $(document.createElement('div'));
        stdOutDiv.addClass('stdout new-section');
        stdOutDiv.attr('output-type', 'stdout');

        outputConsoleFieldset.append(errorDiv);
        outputConsoleFieldset.append(stdErrDiv);
        outputConsoleFieldset.append(stdOutDiv);

        outputConsoleDiv.append(outputConsoleFieldset);
        return outputConsoleDiv;
    }

    function createMarkUp(){
        $pageBody = $('.mgmt-commands-body');
        var selectDiv = createSelectDiv();
        var formWrapperDiv = createFormWrapperDiv();
        var outputConsoleDiv = createOutputConsoleDiv();
        $pageBody.append(selectDiv);
        $pageBody.append(formWrapperDiv);
        $pageBody.append(outputConsoleDiv);
    }

    $(function () {
        createMarkUp();
        loadCommand(0);
    });
})();

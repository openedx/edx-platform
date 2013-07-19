(function () {
    var update = function () {
        // Whenever a value changes create a new serialized version of this
        // problem's inputs and set the hidden input fields value to equal it.
        var parent = $(this).closest('.problems-wrapper');
        // find the closest parent problems-wrapper and use that as the problem
        // grab the input id from the input
        // real_input is the hidden input field
        var real_input = $('input.choicetextvalue', parent);
        var all_inputs = $('.choicetextinput .ctinput', parent);
        var user_inputs = {};
        $(all_inputs).each(function (index, elt) {
            var node = $(elt);
            var name = node.attr('id');
            var val = node.val();
            var radio_value = node.attr('value');
            var type = node.attr('type');
            var is_checked = node.attr('checked');
            if (type === "radio" || type === "checkbox") {
                if (is_checked === "checked" || is_checked === "true") {
                    user_inputs[name] = radio_value;
                }
            } else {
                user_inputs[name] = val;
            }
        });
        var val_string = JSON.stringify(user_inputs);
        //this is what gets submitted as the answer, we deserialize it later
        real_input.val(val_string);
    };

    var check_parent = function (event) {
        // This looks for the containing choice of a textinput
        // and sets it to be checked.
        var elt = $(event.target);
        var parent_container = elt.closest('section[id^="forinput"]');
        var choice = parent_container.find("input[type='checkbox'], input[type='radio']");
        choice.attr("checked", "checked");
        choice.change();
        //need to check it then trigger the change event
    };

    var imitate_label = function (event) {
        // This causes a section to check and uncheck
        // a radiobutton/checkbox whenever a user clicks on it
        // If the button/checkbox is disabled, nothing happens
        var elt = $(event.target);
        var parent_container = elt.closest('section[id^="forinput"]');
        var choice = parent_container.find("input[type='checkbox'], input[type='radio']");
            if (choice.attr("type") === "radio") {
                choice.attr("checked", "checked");
            } else {
                if (choice.attr('checked')) {
                    choice.prop("checked", false);
                } else {
                    choice.prop("checked", true);
                }

            }
            choice.change();
            update();

    };
    var choices = $('.mock_label');
    var inputs = $('.choicetextinput .ctinput');
    var text_inputs = $('.choicetextinput .ctinput[type="text"]');
    // update on load
    inputs.each(update);
    // and on every change
    // This allows text inside of choices to behave as if they were part of
    // a label for the choice's button/checkbox
    choices.click(imitate_label);
    inputs.bind("change", update);
    text_inputs.click(check_parent);
}).call(this);

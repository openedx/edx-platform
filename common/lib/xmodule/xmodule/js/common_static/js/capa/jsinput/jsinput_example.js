/* globals Channel */

(function() {
    'use strict';

    // state will be populated via initial_state via the `setState` method. Defining dummy values here
    // to make the expected structure clear.
    var state = {
            availableChoices: [],
            selectedChoice: ''
        },
        channel,
        select = document.getElementsByClassName('choices')[0],
        feedback = document.getElementsByClassName('feedback')[0];

    function populateSelect() {
        // Populate the select from `state.availableChoices`.
        var i, option;

        // Clear out any pre-existing options.
        while (select.firstChild) {
            select.removeChild(select.firstChild);
        }

        // Populate the select with the available choices.
        for (i = 0; i < state.availableChoices.length; i++) {
            option = document.createElement('option');
            option.value = i;
            option.innerHTML = state.availableChoices[i];
            if (state.availableChoices[i] === state.selectedChoice) {
                option.selected = true;
            }
            select.appendChild(option);
        }
        feedback.innerText = "The currently selected answer is '" + state.selectedChoice + "'.";
    }

    function getGrade() {
        // The following return value may or may not be used to grade server-side.
        // If getState and setState are used, then the Python grader also gets access
        // to the return value of getState and can choose it instead to grade.
        return JSON.stringify(state.selectedChoice);
    }

    function getState() {
        // Returns the current state (which can be used for grading).
        return JSON.stringify(state);
    }

    // This function will be called with 1 argument when JSChannel is not used,
    // 2 otherwise. In the latter case, the first argument is a transaction
    // object that will not be used here
    // (see http://mozilla.github.io/jschannel/docs/)
    function setState() {
        var stateString = arguments.length === 1 ? arguments[0] : arguments[1];
        state = JSON.parse(stateString);
        populateSelect();
    }

    // Establish a channel only if this application is embedded in an iframe.
    // This will let the parent window communicate with this application using
    // RPC and bypass SOP restrictions.
    if (window.parent !== window) {
        channel = Channel.build({
            window: window.parent,
            origin: '*',
            scope: 'JSInput'
        });

        channel.bind('getGrade', getGrade);
        channel.bind('getState', getState);
        channel.bind('setState', setState);
    }

    select.addEventListener('change', function() {
        state.selectedChoice = select.options[select.selectedIndex].text;
        feedback.innerText = "You have selected '" + state.selectedChoice +
            "'. Click Submit to grade your answer.";
    });

    return {
        getState: getState,
        setState: setState,
        getGrade: getGrade
    };
}());

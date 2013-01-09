(function () {
    var timeout = 100;

    waitForJSMolCalc();

    // FIXME: [rocha] jsmolcalc and jsmol.API should be initialized
    // automatically by the GWT script loader. However, it is not
    // working correcly when including them inside the
    // courseware.
    function waitForJSMolCalc() {
        if (typeof(jsmolcalc) != "undefined" && jsmolcalc)
        {
            // FIXME: [rocha] this should be called automatically by
            // GWT at the end of the loader. However it is not.
            jsmolcalc.onInjectionDone('jsmolcalc');
        }

        if (typeof(jsmol) != "undefined") {
            // ready, initialize applets
            initializeApplets();
        } else {
            setTimeout(function() { waitForJSMolCalc(); }, timeout);
        }
    }

    function initializeApplets() {
        var applets = $('.editamoleculeinput object');
        applets.each(function(i, element) {
            var applet = $(element);
            if (!applet.hasClass('initialized')) {
                applet.addClass("initialized");
                waitForApplet(applet, configureApplet);
            }
        });
    }

    function waitForApplet(applet, callback) {
        if (applet[0].isActive && applet[0].isActive()) {
            callback(applet);
        } else {
            setTimeout(function() {
                waitForApplet(applet, callback); }, timeout);
        }
    }

    function configureApplet(applet) {
        // Traverse up the DOM tree and get the other relevant elements
        var parent = applet.parent();
        var input_field = parent.find('input[type=hidden]');
        var reset_button = parent.find('button.reset');

        console.log(input_field.toArray());
        console.log(input_field.toArray().length);

        // Load initial data
        var value = input_field.val();

        value = false;
        if (value) {
            console.log('loading old');
            var data = JSON.parse(value)["mol"];
            console.log(data);
            loadAppletData(applet, data, input_field);
        } else {
            console.log('loading preset');
            requestAppletData(applet, input_field);
        }

        reset_button.on('click', function() {
            console.log('reseting');
            requestAppletData(applet, input_field);
        });

        // FIXME: [rocha] This is a hack to capture the click on the check
        // button and update the hidden field with the applet values
        var problem = applet.parents('.problem');
        var check_button = problem.find('input.check');
        check_button.on('click', function() {
            console.log('check');
            updateInput(applet, input_field);
        });
    }

    function requestAppletData(applet, input_field) {
        var molFile = applet.find('param[name=molfile]').attr('value');

        jQuery.ajax({
            url: molFile,
            dataType: "text",
            success: function(data) {
                console.log("Done.");
                loadAppletData(applet, data, input_field);
            },
            error: function() {
                console.error("Cannot load mol data.");
            }
        });
    }

    function loadAppletData(applet, data, input_field) {
        applet[0].readMolFile(data);
        updateInput(applet, input_field);
    }

    function updateInput(applet, input_field) {
        var mol = applet[0].molFile();
        var smiles = applet[0].smiles();
        var jme = applet[0].jmeFile();

        var info = formatInfo(jsmol.API.getInfo(mol, smiles, jme).toString());
        var value = { mol: mol, info: info };

        console.log("Molecule info:");
        console.log(info);

        input_field.val(JSON.stringify(value));

        return value;
    }

    function formatInfo(info) {
        var results = [];

        var fragment = $('<div>').append(info);
        fragment.find('font').each(function () {
            results.push($(this).html());
        });

        return results;
    }

}).call(this);

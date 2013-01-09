(function () {
    var timeout = 100;

    var applets = $('.editamoleculeinput object');
    var input_field = $('.editamoleculeinput input');
    var reset_button = $('.editamoleculeinput button.reset');

    console.log('EDIT A MOLECULE');

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
            // ready, initialize applets,
            applets.each(function(i, el) { initializeApplet(el); });
        } else if (timeout > 30 * 1000) {
            console.error("JSMolCalc did not load on time.");
        } else {
            console.log("Waiting for JSMolCalc...");
            setTimeout(function() {
                waitForJSMolCalc(); }, timeout);
        }
    }

    function initializeApplet(applet) {
        console.log("Initializing applet..." );
        waitForApplet(applet, configureApplet);
    }

    function waitForApplet(applet, callback) {
        if (applet.isActive && applet.isActive()) {
            console.log("Applet is ready.");
            callback(applet);
        } else if (timeout > 30 * 1000) {
            console.error("Applet did not load on time.");
        } else {
            console.log("Waiting for applet...");
            setTimeout(function() {
                waitForApplet(applet, callback); }, timeout);
        }
    }

    function configureApplet(applet) {
        var value = input_field.val();

        if (value) {
            console.log('Loading previous mol data...');
            var data = JSON.parse(value)["mol"];
            loadAppletData(applet, data);
        } else {
            requestAppletData(applet);
        }

        reset_button.on('click', function() { requestAppletData(applet); });

        // FIXME: [rocha] This is a hack to capture the click on the check
        // button and update the hidden field with the applet values
        var check_button = $(applet).parents('.problem').find('input.check');
        check_button.on('click', function() { updateInput(applet); });
    }

    function requestAppletData(applet) {
        var molFile = $(applet).find('param[name=molfile]').attr('value');

        console.log("Loading mol data from " + molFile + " ...");
        jQuery.ajax({
            url: molFile,
            dataType: "text",
            success: function(data) {
                console.log("Done.");
                loadAppletData(applet, data);
            },
            error: function() {
                console.error("Cannot load mol data.");
            }
        });
    }

    function loadAppletData(applet, data) {
        applet.readMolFile(data);
        updateInput(applet);
    }

    function getAppletInfo(applet) {
        var mol = applet.molFile();
        var smiles = applet.smiles();
        var jme = applet.jmeFile();

        return jsmol.API.getInfo(mol, smiles, jme);
    }

    function updateInput(applet) {
        var mol = applet.molFile();
        var smiles = applet.smiles();
        var jme = applet.jmeFile();

        var info = formatInfo(jsmol.API.getInfo(mol, smiles, jme).toString());
        var value = { mol: mol, info: info };

        console.log("Molecule info:");
        console.log(info);

        input_field.val(JSON.stringify(value));

        return value;
    }

    function formatInfo(info) {
        var results = [];
        // create a te
        var fragment = $('<div>').append(info);
        fragment.find('font').each(function () {
            results.push($(this).html());
        });

        return results;
    }

}).call(this);

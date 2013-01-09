(function () {
    var timeout = 1000;

    function initializeApplet(applet) {
        console.log("Initializing " + applet);
        waitForApplet(applet);
    }

    function waitForApplet(applet) {
        if (applet.isActive && applet.isActive()) {
            console.log("Applet is ready.");
            requestAppletData(applet);
        } else if (timeout > 30 * 1000) {
            console.error("Applet did not load on time.");
        } else {
            console.log("Waiting for applet...");
            setTimeout(function() { waitForApplet(applet); }, timeout);
        }
    }

    function requestAppletData(applet) {
        var file = $(applet).find('param[name=file]').attr('value');

        console.log("Getting file url...");
        console.log(file);

        console.log("Loading mol data...");
        jQuery.ajax({
            url: file,
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
        updateAppletInfo(applet);
    }

    function updateAppletInfo(applet) {
        var info = getAppletInfo(applet);
        console.log(info.toString());
        return info;
    }

    function getAppletInfo(applet) {
        var mol = applet.molFile();
        var smiles = applet.smiles();
        var jme = applet.jmeFile();

        return jsmol.API.getInfo(mol, smiles, jme);
    }

    console.log('EDIT A MOLECULE');

    // FIXME: [rocha] This should be called automatically by the GWT
    // script loader, but for some reason it is not.
    jsmolcalc.onInjectionDone('jsmolcalc');

    // FIXME: [rocha] This is a hack to capture the click on the check
    // button and update the hidden field with the applet values
    var check = $('.editamoleculeinput').parents('.problem').find('input.check');
    check.on('click', function() {console.log("CLICK");});

    // TODO: [rocha] add function to update hidden field
    // TODO: [rocha] load state from hidden field if available

    // initialize applet
    var applets = $('.editamoleculeinput object');
    applets.each(function(i, el) { initializeApplet(el); });

}).call(this);

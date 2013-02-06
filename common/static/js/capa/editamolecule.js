(function () {
    var timeout = 100;

    // Simple "lock" to prevent applets from being initialized more than once
    if (typeof(_editamolecule_loaded) == 'undefined') {
        _editamolecule_loaded = true;
        loadGWTScripts();
        waitForGWT();
    } else {
        return;
    }

    function loadScript(src) {
        var script = document.createElement('script');
        script.setAttribute('type', 'text/javascript');
        script.setAttribute('src',  src);
        $('head')[0].appendChild(script);
    }

    function loadGWTScripts() {
        // The names of the script are split to prevent them from
        // being rewritten by LMS. GWT uses the filename of the script
        // to find the URL path in which the script lives. If the name
        // of the file is changed, GWT won't load correctly
        var jsmolcalc_src = '/sta' + 'tic/js/capa/jsmolcalc/jsmolcalc.nocache.js';
        var jsme_src = '/sta' + 'tic/js/capa/jsme/jsme_export.nocache.js';

        // Make sure we don't request the scripts twice

        if (typeof (_jsmolcalc) == 'undefined') {
            _jsmolcalc = true;
            loadScript(jsmolcalc_src);
        }

        if (typeof (_jsme) == 'undefined') {
            _jsme = true;
            loadScript(jsme_src);
        }
    }

    function waitForGWT() {
        // jsme and jsmolcalc are not initialized automatically by the GWT
        // script loader. To fix this, wait for the scripts to load,
        // initialize them manually and wait until they are ready

        if (typeof(jsmolcalc) != 'undefined' && jsmolcalc)
        {
            jsmolcalc.onInjectionDone('jsmolcalc');
        }

        if (typeof(jsme_export) != 'undefined' && jsme_export)
        {
            // dummy function called by jsme_export
            window.jsmeOnLoad  = function() {};
            jsme_export.onInjectionDone('jsme_export');
        }

        // jsmol is defined my jsmolcalc and JavaScriptApplet is defined by jsme
        if (typeof(jsmol) != 'undefined' && typeof(JavaScriptApplet) != 'undefined') {
            // ready, initialize applets
            initializeApplets();
            _editamolecule_loaded = false;
        } else {
            setTimeout(waitForGWT, timeout);
        }
    }

    function initializeApplets() {
        var applets = $('.editamoleculeinput div.applet');
        applets.each(function(i, element) {
            if (!$(element).hasClass('loaded')) {
                var applet = new JavaScriptApplet.JSME(
                    element.id,
                    $(element).width(),
                    $(element).height(),
                    {
    	                "options" : "query, hydrogens"
    	            });
                $(element).addClass('loaded');
                configureApplet(element, applet);
            }
        });
    }

    function configureApplet(element, applet) {
        // Traverse up the DOM tree and get the other relevant elements
        var parent = $(element).parent();
        var input_field = parent.find('input[type=hidden]');
        var reset_button = parent.find('button.reset');

        // Add div for error messages
        $('<br/> <br/> <div class="errormsgs" style="padding: 5px 5px 5px 5px;\
                visibility:hidden; background-color:#FA6666; height:60px;\
                width:400px;"> </div>').appendTo(parent);

        // Applet options
        applet.setAntialias(true);

        // Load initial data
        var value = input_field.val();
        if (value) {
            var data = JSON.parse(value)["mol"];
            loadAppletData(applet, data, input_field);
        } else {
            requestAppletData(element, applet, input_field);
        }

        reset_button.on('click', function() {
            requestAppletData(element, applet, input_field);

            // Make sure remaining error messages are cleared
            var errordiv = $(element).parent().find('.errormsgs')[0];
            errordiv.style.visibility = 'hidden';
        });

        // Update the input element everytime the is an interaction
        // with the applet (click, drag, etc)
        $(element).on('mouseup', function() {
            updateInput(applet, input_field, element);
        });
    }

    function requestAppletData(element, applet, input_field) {
        var molFile = $(element).data('molfile-src');
        jQuery.ajax({
            url: molFile,
            dataType: "text",
            success: function(data) {
                loadAppletData(applet, data, input_field);
            },
            error: function() {
                console.error("Cannot load mol data from: " + molFile);
            }
        });
    }

    function loadAppletData(applet, data, input_field) {
        applet.readMolFile(data);
        updateInput(applet, input_field);
    }

    function updateInput(applet, input_field, element) {
        var mol = applet.molFile();
        var smiles = applet.smiles();
        var jme = applet.jmeFile();

        var info = formatInfo(jsmol.API.getInfo(mol, smiles, jme).toString(),
                input_field, element);
        var value = { mol: mol, info: info };

        input_field.val(JSON.stringify(value));

        return value;
    }

    function formatInfo(info, input_field, element) {
        var results = [];
        var errordiv = $(element).parent().find('.errormsgs')[0];

        if (!errordiv) {
            // This is a bit hackish, but works.
            // There are situations where formatInfo is called but no div yet exists
            // to my knowledge (blame John Hess) this is always followed by a call to
            // this function once the div does exist
            //console.log("There is no errordiv loaded yet. trying again soon");
            return []
        }

        if (info.search("It is not possible") == -1) {
            errordiv.innerHTML = '';
            errordiv.style.visibility = 'hidden';
            var fragment = $('<div>').append(info);
            fragment.find('font').each(function () {
                results.push($(this).html());
            });
        }
        else {
            // remove Brian's html tags
            var tags = /<((\/)?\w{1,7})>/g;
            var errmsg = info.replace(tags, ' ');

            errordiv.innerHTML = errmsg;
            errordiv.style.visibility = 'visible';
        }

        return results;
    }

}).call(this);

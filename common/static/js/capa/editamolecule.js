(function () {
    var timeout = 100;

    // Simple "lock" to prevent applets from being initialized more than once
    if (typeof(_editamolecule_lock) == 'undefined' || _editamolecule_lock == false) {
        _editamolecule_lock = true;
        waitForGWT();
    } else {
        return;
    }

    // FIXME: [rocha] jsme and jsmolcalc are not initialized automatically by
    // the GWT script loader. To fix this, wait for the scripts to load, initialize
    // them manually and wait until they are ready
    function waitForGWT() {
        if (typeof(jsmolcalc) != "undefined" && jsmolcalc)
        {
            jsmolcalc.onInjectionDone('jsmolcalc');
        }

        if (typeof(jsme_export) != "undefined" && jsme_export)
        {
            // dummy function called by jsme_export
            window.jsmeOnLoad  = function() {};
            jsme_export.onInjectionDone('jsme_export');
        }

        // jsmol is defined my jsmolcalc and JavaScriptApplet is defined by jsme
        if (typeof(jsmol) != 'undefined' && typeof(JavaScriptApplet) != 'undefined') {
            // ready, initialize applets
            initializeApplets();
            _editamolecule_lock = false;  // release lock, for reloading
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
                console.log("Done.");
                loadAppletData(applet, data, input_field);
            },
            error: function() {
                console.error("Cannot load mol data.");
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

        console.log("Molecule info:");
        console.log(info);

        input_field.val(JSON.stringify(value));

        return value;
    }

    function formatInfo(info, input_field, element) {
        var results = [];
        console.log("element parent is"+$(element).parent())
        var errordiv = $(element).parent().find('.errormsgs')[0];
        console.log(errordiv);
        
        if (!errordiv) {
            // This is a bit hackish, but works.
            // There are situations where formatInfo is called but no div yet exists
            // to my knowledge (blame John Hess) this is always followed by a call to
            // this function once the div does exist
            console.log("There is no errordiv loaded yet. trying again soon");
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
            console.log("err");

            // remove Brian's html tags
            var tags = /<((\/)?\w{1,7})>/g;
            var errmsg = info.replace(tags, ' ');
            console.log(errmsg);
            errordiv.innerHTML = errmsg;
            errordiv.style.visibility = 'visible';
        }

        return results;
    }

}).call(this);

$(document).ready(function(){
    var applet = $("#JME")[0];
    var template = _.template($("#task-template").text());
    var timeout = 1000;

    function waitForApplet() {
        if (applet.isActive && applet.isActive()) {
            console.log("Applet is ready.");
            loadInitialData();
        } else if (timeout > 30 * 1000) {
            console.error("Applet did not load on time.");
        } else {
            console.log("Waiting for applet...");
            setTimeout(waitForApplet, timeout);
        }
    }

    function loadInitialData() {
        console.log("Loading mol data...");
        jQuery.ajax({
            url: "dopamine.mol",
            dataType: "text",
            success: function(data) {
                console.log("Done.");
                setup(data);
            },
            error: function() {
                console.error("Cannot load mol data.");
            }
        });
    }

    function setup(data) {
        applet.readMolFile(data);

        setupTasks();

        $("#update").click(updateInfo);
        updateInfo();
    }

    function setupTasks() {
        console.log("Getting initial tasks...");

        var tasks = getTasks();

        jQuery.each(tasks, function(index, task) {
            var value = task.toString();
            var fragment = $(template({task:value}));
            $("#tasks").append(fragment);
            fragment.find("button").click(function() {
                checkTask(task, index);
            });
        });
        console.log("Done.");
    }

    function updateInfo() {
        var info = getInfo();
        $("#properties").html(info.toString());
        return info;
    }

    function checkTask(task, index) {
        var info = updateInfo();
        var value = task.check(info);
        $("#tasks li span.result").eq(index).html(value);
    }

    function getInfo() {
        var mol = applet.molFile();
        var smiles = applet.smiles();
        var jme = applet.jmeFile();

        return jsmol.API.getInfo(mol, smiles, jme);
    }

    function getTasks() {
        var mol = applet.molFile();
        var smiles = applet.smiles();
        var jme = applet.jmeFile();

        return jsmol.API.getTasks(mol, smiles, jme);
    }

    waitForApplet();
});

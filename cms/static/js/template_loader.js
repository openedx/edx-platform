// <!-- from https://github.com/Gazler/Underscore-Template-Loader/blob/master/index.html -->
// TODO Figure out how to initialize w/ static views from server (don't call .load but instead inject in django as strings)
// so this only loads the lazily loaded ones.
(function () {
    if (typeof window.templateLoader == 'function') return;

    var templateLoader = {
        templateVersion: "0.0.15",
        templates: {},
        // Control whether template caching in local memory occurs. Caching screws up development but may
        // be a good optimization in production (it works fairly well).
        cacheTemplates: false,
        loadRemoteTemplate: function (templateName, filename, callback) {
            if (!this.templates[templateName]) {
                var self = this;
                jQuery.ajax({url: filename,
                    success: function (data) {
                        self.addTemplate(templateName, data);
                        self.saveLocalTemplates();
                        callback(data);
                    },
                    error: function (xhdr, textStatus, errorThrown) {
                        console.log(textStatus);
                    },
                    dataType: "html"
                })
            }
            else {
                callback(this.templates[templateName]);
            }
        },

        addTemplate: function (templateName, data) {
            // is there a reason this doesn't go ahead and compile the template? _.template(data)
            // I suppose localstorage use would still req raw string rather than compiled version, but that sd work
            // if it maintains a separate cache of uncompiled ones
            this.templates[templateName] = data;
        },

        localStorageAvailable: function () {
            try {
                return this.cacheTemplates && 'localStorage' in window && window['localStorage'] !== null;
            } catch (e) {
                return false;
            }
        },

        saveLocalTemplates: function () {
            if (this.localStorageAvailable()) {
                localStorage.setItem("templates", JSON.stringify(this.templates));
                localStorage.setItem("templateVersion", this.templateVersion);
            }
        },

        loadLocalTemplates: function () {
            if (this.localStorageAvailable()) {
                var templateVersion = localStorage.getItem("templateVersion");
                if (templateVersion && templateVersion == this.templateVersion) {
                    var templates = localStorage.getItem("templates");
                    if (templates) {
                        templates = JSON.parse(templates);
                        for (var x in templates) {
                            if (!this.templates[x]) {
                                this.addTemplate(x, templates[x]);
                            }
                        }
                    }
                }
                else {
                    localStorage.removeItem("templates");
                    localStorage.removeItem("templateVersion");
                }
            }
        }

    };
    templateLoader.loadLocalTemplates();
    window.templateLoader = templateLoader;
})();

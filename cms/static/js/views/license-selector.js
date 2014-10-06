define(["js/views/baseview", "underscore", "gettext"],
    function(BaseView, _, gettext) {

        var LicenseSelector = BaseView.extend({
            events : {
                "click .license-button" : "onLicenseButtonClick",
            },
            options : {
                buttonSize : false,
                imgSize : false,
            },

            initialize : function() {
                this.template = this.loadTemplate("license-selector");
                this.setLicense(this.model);
            },

            getLicense: function() {
                return this.license;
            },

            setLicense: function(newLicense) {
                this.license = this.validate(newLicense);
                this.$el.find('.license').val(this.license);
                this.$el.find('.selected-license').html(this.img());
                this.setLicenseButtons();
            },

            render: function() {
                this.$el.html(this.template({
                    default_license: this.license,
                    default_license_img: this.img()
                }));

                this.$el.addClass('license-selector');

                if (this.options.buttonSize) {
                    this.$el.find('.license-button').addClass('size-'+this.options.buttonSize);
                }
                this.setLicenseButtons(this.license);

                return this;
            },

            setLicenseButtons : function(license) {
                if (!license) {
                    license = this.getLicense();
                }

                

                this.$el.find('.license-cc .license-button').removeClass('selected');

                if (!license || license == "NONE") {
                    this.$el.find('.license-button').removeClass('selected');
                    this.$el.find('.license-allornothing').removeClass('selected');
                    this.$el.find('.license-cc').removeClass('selected');
                }
                else if (license == "ARR") {
                    this.$el.find('.license-button[data-license="ARR"]').addClass('selected');
                    this.$el.find('.license-button[data-license="CC0"]').removeClass('selected');
                }
                else if (license == "CC0") {
                    this.$el.find('.license-button[data-license="CC0"]').addClass('selected');
                    this.$el.find('.license-button[data-license="ARR"]').removeClass('selected');
                }
                else {
                    var attr = license.split("-");

                    if (attr.length >1 && attr[0]=="CC" && attr[1]=="BY") {
                        for(i in attr) {
                            this.$el.find('.license-button[data-license="'+attr[i]+'"]').addClass('selected');               
                        }
                    }
                }

                // Toggle between custom license and allornothing
                if (license=="ARR" || license=="CC0") {
                    this.$el.find('.license-allornothing').addClass('selected');
                    this.$el.find('.license-cc').removeClass('selected');
                }
                else if (license != "NONE") {
                    this.$el.find('.license-cc').addClass('selected');
                    this.$el.find('.license-allornothing').removeClass('selected').children().removeClass("selected");
                }

                return this;
            },

            validate: function(license) {
                var validLicense;

                if (!license) {
                    validLicense = "NONE";
                }
                else if (license == "ARR" || license == "CC0") {
                    validLicense = license;
                }
                else {
                    var attr = license.split("-");

                    if (attr.length >1 && attr[0]=="CC" && attr[1]=="BY") {
                        validLicense = attr.join("-");
                    }
                    else {
                        validLicense = "NONE";
                    }
                }

                return validLicense;
            },

            img: function() {
                var license = this.license.toLowerCase();
                var imgSize;

                if (this.options.imgSize=="big") {
                    imgSize = "88x31";
                }
                else {
                    imgSize = "80x15";
                }
                
                var img_url = "";
                switch(license) {
                    case "arr":
                        img_url = window.baseUrl+'images/arr/';
                    break;
                    case "cc0":
                        img_url = "http://i.creativecommons.org/l/zero/1.0/";
                    break;
                    case "none":
                        return "None";
                    break;
                    
                    // Creative commons license
                    default:
                    img_url = 'http://i.creativecommons.org/l/' + license.substring(3,license.length) + "/3.0/";

                }

                var img = "<img src='"+img_url+imgSize+".png' />"
             
                return img;
            },

             onLicenseButtonClick : function(e) {
                var $button = $(e.srcElement).closest('.license-button');
                var $allornothing = this.$el.find('.license-allornothing');
                var $cc = this.$el.find('.license-cc');

                var license;
                if($cc.has($button).length==0) {
                    license = $button.attr("data-license");
                }
                else {
                    $button.toggleClass("selected");

                    if ($button.attr("data-license") == "ND" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='SA']").removeClass("selected");
                    }
                    else if($button.attr("data-license") == "SA"&& $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='ND']").removeClass("selected");
                    }

                    if ($button.attr("data-license") == "BY" && !$button.hasClass("selected")) {
                        license = "CC0";
                    }
                    else {
                        license = "CC";
                        $cc.children(".license-button[data-license='BY']").addClass("selected");
                        var selected = $cc.children(".selected");
                        selected.each( function() {
                            license = license + "-" + $(this).attr("data-license");
                        })
                    }

                    
                }

                this.setLicense(license);
                this.setLicenseButtons(license);

                return this;
            },

            });

        return LicenseSelector;
    }); // end define();

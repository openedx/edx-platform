define(["jquery"], function($) {
    var license_to_img = function(license) {
            if (license=="ARR") {
                return "<a target='_blank' href=''><img src='"+window.baseUrl+"images/arr.png' /></a>"
            }
            else if(license=="CC0") {
                license_url = "http://i.creativecommons.org/l/zero/1.0/";
            }
            else {
                var attr = license.toLowerCase().split("-");
                if (attr[0]!="cc") {
                    return "No license.";
                }
                attr = attr.splice(1,attr.length - 1);

                license_url = 'http://i.creativecommons.org/l/' + attr.join("-") + "/3.0/";
            }
            
            img_url = license_url + "80x15.png";
            img = "<a target='_blank' href='"+license_url+"'><img src='"+img_url+"' /></a>"

            return img;

        }

    return license_to_img;
});
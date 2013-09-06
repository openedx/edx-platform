// Fetch data about badges via JSONP, so that the progress page does
// not fail to load if the badge service is failing.

$(document).ready(function() {

    badges_element = $("#badges");

    badges_element.css("position", "relative");
    badges_element.css("text-align", "center");

    // Call render_badges.
    render_badges();

});

var render_badges = function() {
    var badge_url = badge_service_url + "/v1/badges/?format=jsonp&email=" + email + "&badgeclass__issuer__course=" + course_id + "&callback=?";
    var badgeclass_url = badge_service_url + "/v1/badgeclasses/?format=jsonp&issuer__course=" + course_id + "&callback=?";

    $.when($.getJSON(badge_url), $.getJSON(badgeclass_url)).done(

        function(badges_data, badgeclasses_data) {

            var badges_list = badges_data[0].results;
            var badgeclasses_list = badgeclasses_data[0].results;

            if (badgeclasses_list.length !== 0) {

                // Add an attribute to each badgeclass for whether it has been earned or not.
                badgeclasses_list = _.map(badgeclasses_list, function(badgeclass) {
                    badgeclass.is_earned = is_earned(badgeclass, badges_list);
                    return badgeclass;
                });

                var data = {
                    "badgeclasses": badgeclasses_list,
                };

                // Render the mustache template in `badges_Element` using the information in `data`.
                // Replace the html in `badges_element` with the new rendered html.
                var template = badges_element.html();
                var badges_html = Mustache.to_html(template, data);
                badges_element.html(badges_html);

                // Unhide the div. (It was hidden to hide the unrendered template)
                badges_element.css('display', 'inline');
            }
        }
    );
};

// Determine whether a badgeclass has been earned -- whether it is in badges_list. Return true or false.
var is_earned = function(badgeclass, badges_list) {
    badgeclass_urls = _.map(badges_list, function(badge) {return badge.badge;});
    badgeclass_url = badgeclass.edx_href + ".json";
    return _.contains(badgeclass_urls, badgeclass_url);
};

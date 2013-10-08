define(["jquery"], function($) {
    var url = "//www.youtube.com/player_api";
    $("head").append($("<script/>", {src: url}));
    return window.YT;
});

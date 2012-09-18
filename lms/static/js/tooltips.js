var $body;
var $tooltip;
var tooltipTimer;
var tooltipCoords;
$(document).ready(function() {
    $body = $('body');
    $tooltip = $('<div class="tooltip"></div>');
    $body.delegate('[data-tooltip]', {
        'mouseover': showTooltip,
        'mousemove': moveTooltip,
        'mouseout': hideTooltip,
        'click': hideTooltip
    });
});

function showTooltip(e) {
    var tooltipText = $(this).attr('data-tooltip');
    $tooltip.html(tooltipText);
    $body.append($tooltip);
    $(this).children().css('pointer-events', 'none');

    tooltipCoords = {
        x: e.pageX - ($tooltip.outerWidth() / 2),
        y: e.pageY - ($tooltip.outerHeight() + 15)
    };

    $tooltip.css({
        'left': tooltipCoords.x,
        'top': tooltipCoords.y
    });

    tooltipTimer = setTimeout(function() {
        $tooltip.show().css('opacity', 1);

        tooltipTimer = setTimeout(function() {
            hideTooltip();
        }, 3000);
    }, 500);
}

function moveTooltip(e) {
    tooltipCoords = {
        x: e.pageX - ($tooltip.outerWidth() / 2),
        y: e.pageY - ($tooltip.outerHeight() + 15)
    };

    $tooltip.css({
        'left': tooltipCoords.x,
        'top': tooltipCoords.y
    });
}

function hideTooltip(e) {
    $tooltip.hide().css('opacity', 0);
    clearTimeout(tooltipTimer);
}

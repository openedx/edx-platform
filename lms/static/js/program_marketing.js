function paginate(page, size, total) {
    'use strict';
    var start = size * page,
        end = (start + size - 1) >= total ? total - 1 : (start + size - 1);
    $('.profile-item-desktop').each(function(index, item) {
        if (index >= start && index <= end) {
            $(item).css('display', 'block');
        } else {
            $(item).css('display', 'none');
        }
    });
    $('.pagination-start').text(start + 1);
    $('.pagination-end').text(end + 1);
}

$(document).ready(function() {
    'use strict';
    // Custom function showing current slide
    var $status = $('.pagingInfo');

    // Instructor pagination
    var page = 0,
        size = 4,
        total = parseInt($('.instructor-size').text(), 10),
        maxPages = Math.ceil(total / size) - 1;

    paginate(page, size, total);

    // Initialize FAQ
    $('ul.faq-links-list li.item').click(function() {
        if ($(this).find('.answer').hasClass('hidden')) {
            $(this).find('.answer').removeClass('hidden');
            $(this).addClass('expanded');
        } else {
            $(this).find('.answer').addClass('hidden');
            $(this).removeClass('expanded');
        }
    });

    if (page < maxPages) {
        $('#pagination-next').addClass('active');
    }

    $('#pagination-next').click(function() {
        if (page === maxPages) {
            return false;
        }
        if (page + 1 === maxPages) {
            $(this).removeClass('active');
        }
        page = page + 1;
        paginate(page, size, total);
        $('#pagination-previous').addClass('active');
        return false;
    });

    $('#pagination-previous').click(function() {
        if (page === 0) {
            return false;
        }
        if (page - 1 === 0) {
            $(this).removeClass('active');
        }
        page = page - 1;
        paginate(page, size, total);
        $('#pagination-next').addClass('active');
        return false;
    });

    $('#accordion-group').accordion({
        header: '> .accordion-item > .accordion-head',
        collapsible: true,
        active: false,
        heightStyle: 'content'
    });
});

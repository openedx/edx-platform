(function () {
    function confirmAndSubmit(e) {
        var $target = $(e.target);
        var args = $target.siblings('input').val();
        var fmt = gettext('Are you sure you want to execute the command: %(command)s with arguments: %(args)s ?');
        var confirmMessage = interpolate(fmt, {
            command: $target.val(),
            args: args
        }, true);
        if (confirm(confirmMessage)) {
            var $form = $('.sysadmin-dashboard-wrapper .sysadmin-course-tabs-form');
            var $hiddenInput = $(document.createElement('input'));
            $hiddenInput.attr({
                type: 'hidden',
                name: 'action'
            });
            $hiddenInput.val($target.val());
            $hiddenInput.appendTo($form);
            $form.submit();
        }
    }

    $(function () {
        $('.edit-course-tabs .insert-tab-button').click(confirmAndSubmit);
        $('.edit-course-tabs .delete-tab-button').click(confirmAndSubmit);
    });
})();

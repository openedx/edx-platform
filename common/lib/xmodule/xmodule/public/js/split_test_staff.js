
/**
 * Creates a new selector for managing toggling which child to show
 * @constructor
 */

function ABTestSelector(elem) {
    me = this;
    me.elem = $(elem);

    select_child = function(group_id) {
        // iterate over all the children and hide all the ones that haven't been selected
        // and show the one that was selected
        me.elem.find('.split-test-child').each(function() {
            // force this id to remain a string, even if it looks like something else
            child_group_id = $(this).data('group-id').toString();
            if(child_group_id === group_id) {
                $(this).show();
            }
            else {
                $(this).hide();
            }

        });
    }

    // hide all the children
    me.elem.find('.split-test-child').hide();

    select = me.elem.find('.split-test-select');
    cur_group_id = select.val();
    select_child(cur_group_id);

    // bind the change event to the dropdown
    select.change(function() {
        group_id = $(this).val()
        select_child(group_id);
    });

}




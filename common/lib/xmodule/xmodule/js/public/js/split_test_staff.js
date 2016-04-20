
/**
 * Creates a new selector for managing toggling which child to show
 * @constructor
 */

function ABTestSelector(runtime, elem) {
    var _this = this;
    _this.elem = $(elem);
    _this.children = _this.elem.find('.split-test-child');
    _this.content_container = _this.elem.find('.split-test-child-container');

    function select_child(group_id) {
        // iterate over all the children and hide all the ones that haven't been selected
        // and show the one that was selected
        _this.children.each(function() {
            // force this id to remain a string, even if it looks like something else
            var child_group_id = $(this).data('group-id').toString();
            if(child_group_id === group_id) {
                _this.content_container.html($(this).text());
                XBlock.initializeBlocks(_this.content_container, $(elem).data('request-token'));
            }
        });
    }

    select = _this.elem.find('.split-test-select');
    cur_group_id = select.val();
    select_child(cur_group_id);

    // bind the change event to the dropdown
    select.change(function() {
        group_id = $(this).val()
        select_child(group_id);
    });

}




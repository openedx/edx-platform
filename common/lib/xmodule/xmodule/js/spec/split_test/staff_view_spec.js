describe('Tests for split_test staff view switching', function() {
    var ab_module;
    var elem;
    beforeEach(function() {
        loadFixtures('split_test_staff.html');
        elem = $('#split-test');
        ab_module = ABTestSelector(null, elem);
    });

    it("test that we have only one visible condition", function() {
        var num_visible = 0;
        elem.find('.split-test-child').each(function() {
            if($(this).is(':visible')) {
                num_visible++;
            }
        });
        expect(num_visible).toEqual(1);

    });

    it("test that the right child is visible when selected", function() {
        var groups = ['0', '1', '2'];

        for(var i = 0; i < groups.length; i++) {
            var to_select = groups[i];
            elem.find('.split-test-select').val(to_select).change();
            elem.find('.split-test-child').each(function() {
                if($(this).data('group-id').toString() === to_select) {
                    expect($(this).is(':visible')).toBeTruthy();
                }
                else {
                    expect($(this).is(':visible')).toBeFalsy();
                }
            });
        }

    });

});

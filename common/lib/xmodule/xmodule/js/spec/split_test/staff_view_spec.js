describe('Tests for split_test staff view switching', function() {
    var ab_module;
    var elem;

    beforeEach(function() {
        loadFixtures('split_test_staff.html');
        elem = $('#split-test');
        window.XBlock = jasmine.createSpyObj('XBlock', ['initializeBlocks']);
        ab_module = ABTestSelector(null, elem);
    });

    afterEach(function() {
        delete window.XBlock;
    });

    it("test that we have only one visible condition", function() {
        var containers = elem.find('.split-test-child-container').length;
        var conditions_shown = elem.find('.split-test-child-container .condition-text').length;
        expect(containers).toEqual(1);
        expect(conditions_shown).toEqual(1);
        expect(XBlock.initializeBlocks).toHaveBeenCalled();
    });

    it("test that the right child is visible when selected", function() {
        var groups = ['0', '1', '2'];

        for(var i = 0; i < groups.length; i++) {
            var to_select = groups[i];
            elem.find('.split-test-select').val(to_select).change();
            var child_text = elem.find('.split-test-child-container .condition-text').text();
            expect(child_text).toContain(to_select);
            expect(XBlock.initializeBlocks).toHaveBeenCalled();
        }

    });

});

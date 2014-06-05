describe("JSInput", function() {
    beforeEach(function () {
        loadFixtures('js/capa/fixtures/jsinput.html');
    });

    it('sets all data-processed attributes to true on first load', function() {
        var sections = $(document).find('section[id="inputtype_"]');
        JSInput.walkDOM();
        sections.each(function(index, section) {
            expect(section.attr('data-processed')).toEqual('true');
        });
    });

    it('sets the data-processed attribute to true on subsequent load', function() {
        var section1 = $(document).find('section[id="inputtype_1"]'),
            section2 = $(document).find('section[id="inputtype_2"]');
        section1.attr('data-processed', false);
        JSInput.walkDOM();
        expect(section1.attr('data-processed')).toEqual('true');
        expect(section2.attr('data-processed')).toEqual('true');
    });

    it('sets the waitfor attribute to its update function', function() {
        var inputFields = $(document).find('input[id="input_"]');
        JSInput.walkDOM();
        inputFields.each(function(index, inputField) {
            expect(inputField.data('waitfor')).toBeDefined();
        });
    });

    it('tests the correct number of sections', function () {
        var sections = $(document).find('section[id="inputtype_"]');
        var inputFields = $(document).find('input[id="input_"]');
        expect(sections.length).toEqual(2);
        expect(sections.length).toEqual(inputFields.length);
    });
});


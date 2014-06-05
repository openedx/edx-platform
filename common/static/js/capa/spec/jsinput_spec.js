describe("JSInput", function () {
    var sections;
    var inputFields;

    beforeEach(function () {
        loadFixtures('js/capa/fixtures/jsinput.html');
        sections = $('section[id^="inputtype_"]');
        inputFields = $('input[id^="input_"]');
        JSInput.walkDOM();
    });

    it('sets all data-processed attributes to true on first load', function () {
        sections.each(function (index, item) {
            expect(item).toHaveData('processed', true);
        });
    });

    it('sets the data-processed attribute to true on subsequent load', function() {
        var section1 = $(this.sections[0]);
        var section2 = $(this.sections[1]);
        section1.attr('data-processed', false);
        JSInput.walkDOM();
        expect(section1.attr('data-processed')).toEqual('true');
        expect(section2.attr('data-processed')).toEqual('true');
    });

    it('sets the waitfor attribute to its update function', function () {
        inputFields.each(function (index, item) {
            expect(item).toHaveAttr('waitfor');
        });
    });

    it('tests the correct number of sections', function () {
        expect(sections.length).toEqual(2);
        expect(sections.length).toEqual(inputFields.length);
    });
});


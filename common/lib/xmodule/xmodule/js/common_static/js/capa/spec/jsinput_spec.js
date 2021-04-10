describe('JSInput', function() {
    var $jsinputContainers;
    var $inputFields;

    beforeEach(function() {
        loadFixtures('js/capa/fixtures/jsinput.html');
        $jsinputContainers = $('.jsinput');
        $inputFields = $('input[id^="input_"]');
        JSInput.walkDOM();
    });

    it('sets all data-processed attributes to true on first load', function() {
        $jsinputContainers.each(function(index, item) {
            expect(item).toHaveData('processed', true);
        });
    });

    it('sets the waitfor attribute to its update function', function() {
        $inputFields.each(function(index, item) {
            expect(item).toHaveAttr('waitfor');
        });
    });

    it('tests the correct number of jsinput instances', function() {
        expect($jsinputContainers.length).toEqual(2);
        expect($jsinputContainers.length).toEqual($inputFields.length);
    });
});


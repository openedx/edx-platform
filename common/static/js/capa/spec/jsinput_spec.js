xdescribe("A jsinput has:", function () {

    beforeEach(function () {
        $('#fixture').remove();
        $.ajax({
            async: false,
            url: 'mainfixture.html',
            success: function(data) {
                $('body').append($(data));
            }
        });
    });



    describe("The jsinput constructor", function(){

        var iframe1 = $(document).find('iframe')[0];

        var testJsElem = jsinputConstructor({
            id: 1,
            elem: iframe1,
            passive: false
        });

        it("Returns an object", function(){
            expect(typeof(testJsElem)).toEqual('object');
        });

        it("Adds the object to the jsinput array", function() {
            expect(jsinput.exists(1)).toBe(true);
        });

        describe("The returned object", function() {

            it("Has a public 'update' method", function(){
                expect(testJsElem.update).toBeDefined();  
            });

            it("Returns an 'update' that is idempotent", function(){
                var orig = testJsElem.update();
                for (var i = 0; i++; i < 5) {
                    expect(testJsElem.update()).toEqual(orig);
                }
            });

            it("Changes the parent's inputfield", function() {
                testJsElem.update();
              
            });
        });
    });


    describe("The walkDOM functions", function() {

        walkDOM();

        it("Creates (at least) one object per iframe", function() {
            jsinput.arr.length >= 2; 
        });

        it("Does not create multiple objects with the same id", function() {
            while (jsinput.arr.length > 0) {
                var elem = jsinput.arr.pop();
                expect(jsinput.exists(elem.id)).toBe(false);
            }
        });
    });
})

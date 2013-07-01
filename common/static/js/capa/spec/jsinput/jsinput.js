describe("A jsinput has:", function () {

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

    describe("The ctxCall function", function() {
        it("Evaluatates nested-object functions", function() {
            var ctxTest = {
                ctxFn : function () {
                    return this.name ;
                }
            };
            var fnString = "nest.ctxFn";
            var holder = {};
            holder.nest = ctxTest;
            var fn = _ctxCall(holder, fnString);
            expect(fnString).toBe(holder.nest.ctxFn());
        });

        it("Throws an exception when the object does not exits", function () {
            var notObj = _ctxCall("twas", "brilling");
            expect(notObj).toThrow();
        });

        it("Throws an exception when the function does not exist", function () {
            var anobj = {};
            var notFn = _ctxCall("anobj", "brillig");
            expect(notFn).toThrow();
        });


    });

    describe("The jsinput constructor", function(){
        var testJsElem = jsinputConstructor({
            id: 3781,
            elem: "<div id='abc'> a div </div>",
            passive: false
        });

        it("Returns an object", function(){
            expect(typeof(testJsElem)).toEqual('object');
        });

        it("Adds the object to the jsinput array", function() {
            expect(jsinput.jsinputarr.exists(3781)).toBe(true);
        });

        describe("The returned object", function() {

            it("Has a public 'update' method", function(){
                expect(testJsElem.update).toBeDefined();  
            });

            it("Changes the parent's inputfield", function() {
              
            })

        });

    });
}
        )

define(
    [
        "jquery", "underscore",
        "js/views/baseview",
        "js/utils/handle_iframe_binding",
        "sinon"
    ],
function ($, _, BaseView, IframeBinding, sinon) {

    describe("BaseView check", function () {
        var baseView;
        var iframeBinding_spy;

        beforeEach(function () {
            iframeBinding_spy = sinon.spy(IframeBinding, "iframeBinding");
            baseView = BaseView.prototype;

            spyOn(baseView, 'initialize');
            spyOn(baseView, 'beforeRender');
            spyOn(baseView, 'render');
            spyOn(baseView, 'afterRender').andCallThrough();
        });

        afterEach(function () {
            iframeBinding_spy.restore();
        });

        it('calls before and after render functions when render of baseview is called', function () {
            var baseview_temp = new BaseView()
            baseview_temp.render();

            expect(baseView.initialize).toHaveBeenCalled();
            expect(baseView.beforeRender).toHaveBeenCalled();
            expect(baseView.render).toHaveBeenCalled();
            expect(baseView.afterRender).toHaveBeenCalled();
        });

        it('calls iframeBinding function when afterRender of baseview is called', function () {
            var baseview_temp = new BaseView()
            baseview_temp.render();
            expect(baseView.afterRender).toHaveBeenCalled();
            expect(iframeBinding_spy.called).toEqual(true);

            //check calls count of iframeBinding function
            expect(iframeBinding_spy.callCount).toBe(1);
            IframeBinding.iframeBinding();
            expect(iframeBinding_spy.callCount).toBe(2);
        });
    });
});

define([ "jquery", "js/spec_helpers/create_sinon", "URI", "js/views/container", "js/models/xblock_info",
    "js/views/feedback_notification", "jquery.simulate",
    "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],
    function ($, create_sinon, URI, ContainerView, XBlockInfo, Notification) {

        describe("Container View", function () {

            describe("Supports reordering components", function () {

                var model, containerView, mockContainerHTML, respondWithMockXBlockFragment,
                    init, dragHandleVertically, dragHandleOver, verifyRequest, verifyNumReorderCalls,
                    respondToRequest,

                    rootLocator = 'testCourse/branch/draft/split_test/splitFFF',
                    containerTestUrl = '/xblock/' + rootLocator,

                    groupAUrl = "/xblock/locator-group-A",
                    groupA = "locator-group-A",
                    groupAComponent1 = "locator-component-A1",
                    groupAComponent2 = "locator-component-A2",
                    groupAComponent3 = "locator-component-A3",

                    groupBUrl = "/xblock/locator-group-B",
                    groupB = "locator-group-B",
                    groupBComponent1 = "locator-component-B1",
                    groupBComponent2 = "locator-component-B2",
                    groupBComponent3 = "locator-component-B3";

                rootLocator = 'testCourse/branch/draft/split_test/splitFFF';
                mockContainerHTML = readFixtures('mock/mock-container-xblock.underscore');

                respondWithMockXBlockFragment = function (requests, response) {
                    var requestIndex = requests.length - 1;
                    create_sinon.respondWithJson(requests, response, requestIndex);
                };

                beforeEach(function () {
                    setFixtures('<div class="wrapper-xblock level-page" data-locator="' + rootLocator + '"></div>');
                    model = new XBlockInfo({
                        id: rootLocator,
                        display_name: 'Test AB Test',
                        category: 'split_test'
                    });

                    containerView = new ContainerView({
                        model: model,
                        view: 'container_preview',
                        el: $('.wrapper-xblock')
                    });
                });

                afterEach(function () {
                    containerView.remove();
                });

                init = function (caller) {
                    var requests = create_sinon.requests(caller);
                    containerView.render();

                    respondWithMockXBlockFragment(requests, {
                        html: mockContainerHTML,
                        "resources": []
                    });

                    $('body').append(containerView.$el);
                    return requests;
                };

                dragHandleVertically = function (index, dy) {
                    var handle = containerView.$(".drag-handle:eq(" + index + ")");
                    handle.simulate("drag", {dy: dy});
                };

                dragHandleOver = function (index, targetElement) {
                    var handle = containerView.$(".drag-handle:eq(" + index + ")"),
                        dy = handle.y - targetElement.y;

                    handle.simulate("drag", {dy: dy});
                };

                verifyRequest = function (requests, reorderCallIndex, expectedURL, expectedChildren) {
                    var request, children, i;
                    // 0th call is the response to the initial render call to get HTML.
                    request = requests[reorderCallIndex + 1];
                    expect(request.url).toEqual(expectedURL);
                    children = (JSON.parse(request.requestBody)).children;
                    expect(children.length).toEqual(expectedChildren.length);
                    for (i = 0; i < children.length; i++) {
                        expect(children[i]).toEqual(expectedChildren[i]);
                    }
                };

                verifyNumReorderCalls = function (requests, expectedCalls) {
                    // Number of calls will be 1 more than expected because of the initial render call to get HTML.
                    expect(requests.length).toEqual(expectedCalls + 1);
                };

                respondToRequest = function (requests, reorderCallIndex, status) {
                    // Number of calls will be 1 more than expected because of the initial render call to get HTML.
                    requests[reorderCallIndex + 1].respond(status);
                };

                it('does nothing if item not moved far enough', function () {
                    var requests = init(this);
                    // Drag the first thing in Group A (text component) down very slightly, but not past second thing.
                    dragHandleVertically(2, 5);
                    verifyNumReorderCalls(requests, 0);
                });

                it('can reorder within a group', function () {
                    var requests = init(this);
                    // Drag the first component in Group A to the end
                    dragHandleVertically(2, 80);
                    respondToRequest(requests, 0, 200);
                    verifyNumReorderCalls(requests, 1);
                    verifyRequest(requests, 0, groupAUrl, [groupAComponent2, groupAComponent3, groupAComponent1]);
                });

                it('can drag from one group to another', function () {
                    var requests = init(this);
                    // Drag the first component in Group A into the second group.
                    dragHandleVertically(2, 300);
                    respondToRequest(requests, 0, 200);
                    respondToRequest(requests, 1, 200);
                    // Will get an event to move into Group B and an event to remove from Group A.
                    verifyNumReorderCalls(requests, 2);
                    verifyRequest(requests, 0, groupBUrl,
                        [groupBComponent1, groupBComponent2, groupAComponent1, groupBComponent3]);
                    verifyRequest(requests, 1, groupAUrl, [groupAComponent2, groupAComponent3]);
                });

                it('does not remove from old group if addition to new group fails', function () {
                    var requests = init(this);
                    // Drag the first component in Group A into the second group.
                    dragHandleVertically(2, 300);
                    respondToRequest(requests, 0, 500);
                    // Send failure for addition to new group-- no removal event should be received.
                    verifyNumReorderCalls(requests, 1);
                    verifyRequest(requests, 0, groupBUrl,
                        [groupBComponent1, groupBComponent2, groupAComponent1, groupBComponent3]);
                });

                it('can swap group A and group B', function () {
                    var requests = init(this);
                    // Drag Group B before group A.
                    dragHandleVertically(5, -300);
                    respondToRequest(requests, 0, 200);
                    verifyNumReorderCalls(requests, 1);
                    verifyRequest(requests, 0, containerTestUrl, [groupB, groupA]);
                });


                it('can drag a component to the top level, and nest one group in another', function () {
                    var requests = init(this);
                    // Drag text item in Group A to the top level (in first position).
                    dragHandleVertically(2, -40);
                    respondToRequest(requests, 0, 200);
                    respondToRequest(requests, 1, 200);
                    verifyNumReorderCalls(requests, 2);
                    verifyRequest(requests, 0, containerTestUrl, [groupAComponent1, groupA, groupB]);
                    verifyRequest(requests, 1, groupAUrl, [groupAComponent2, groupAComponent3]);

                    // Drag Group A into Group B.
                    dragHandleVertically(1, 150);
                    respondToRequest(requests, 2, 200);
                    respondToRequest(requests, 3, 200);
                    verifyNumReorderCalls(requests, 4);
                    verifyRequest(requests, 2, groupBUrl, [groupBComponent1, groupA, groupBComponent2]);
                    verifyRequest(requests, 3, containerTestUrl, [groupAComponent1, groupB]);
                });

                describe("Shows a saving message", function () {
                    var savingSpies;

                    beforeEach(function () {
                        savingSpies = spyOnConstructor(Notification, "Mini",
                            ["show", "hide"]);
                        savingSpies.show.andReturn(savingSpies);
                    });

                    it('hides saving message upon success', function () {
                        var requests, savingOptions;
                        requests = init(this);

                        // Drag the first component in Group A into the second group.
                        dragHandleVertically(2, 200);

                        expect(savingSpies.constructor).toHaveBeenCalled();
                        expect(savingSpies.show).toHaveBeenCalled();
                        expect(savingSpies.hide).not.toHaveBeenCalled();
                        savingOptions = savingSpies.constructor.mostRecentCall.args[0];
                        expect(savingOptions.title).toMatch(/Saving/);

                        respondToRequest(requests, 0, 200);
                        expect(savingSpies.hide).not.toHaveBeenCalled();
                        respondToRequest(requests, 1, 200);
                        expect(savingSpies.hide).toHaveBeenCalled();
                        verifyNumReorderCalls(requests, 2);
                    });

                    it('does not hide saving message if failure', function () {
                        var requests = init(this);

                        // Drag the first component in Group A into the second group.
                        dragHandleVertically(2, 200);

                        expect(savingSpies.constructor).toHaveBeenCalled();
                        expect(savingSpies.show).toHaveBeenCalled();
                        expect(savingSpies.hide).not.toHaveBeenCalled();

                        respondToRequest(requests, 0, 500);
                        expect(savingSpies.hide).not.toHaveBeenCalled();
                        // Since the first reorder call failed, the removal will not be called.
                        verifyNumReorderCalls(requests, 1);
                    });
                });
            });
        });
    });
147
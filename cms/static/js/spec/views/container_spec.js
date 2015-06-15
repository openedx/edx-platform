define([ "jquery", "common/js/spec_helpers/ajax_helpers", "js/spec_helpers/edit_helpers",
    "js/views/container", "js/models/xblock_info", "jquery.simulate",
    "xmodule", "coffee/src/main", "xblock/cms.runtime.v1"],
    function ($, AjaxHelpers, EditHelpers, ContainerView, XBlockInfo) {

        describe("Container View", function () {

            describe("Supports reordering components", function () {

                var model, containerView, mockContainerHTML, respondWithMockXBlockFragment, init, getComponent,
                    getDragHandle, dragComponentVertically, dragComponentAbove,
                    verifyRequest, verifyNumReorderCalls, respondToRequest, notificationSpy,

                    rootLocator = 'locator-container',
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

                mockContainerHTML = readFixtures('mock/mock-container-xblock.underscore');

                respondWithMockXBlockFragment = function (requests, response) {
                    var requestIndex = requests.length - 1;
                    AjaxHelpers.respondWithJson(requests, response, requestIndex);
                };

                beforeEach(function () {
                    EditHelpers.installMockXBlock();
                    EditHelpers.installViewTemplates();
                    appendSetFixtures('<div class="wrapper-xblock level-page studio-xblock-wrapper" data-locator="' + rootLocator + '"></div>');
                    notificationSpy = EditHelpers.createNotificationSpy();
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
                    EditHelpers.uninstallMockXBlock();
                    containerView.remove();
                });

                init = function (caller) {
                    var requests = AjaxHelpers.requests(caller);
                    containerView.render();

                    respondWithMockXBlockFragment(requests, {
                        html: mockContainerHTML,
                        "resources": []
                    });

                    $('body').append(containerView.$el);

                    // Give the whole container enough height to contain everything.
                    $('.xblock[data-locator=locator-container]').css('height', 2000);

                    // Give the groups enough height to contain their child vertical elements.
                    $('.is-draggable[data-locator=locator-group-A]').css('height', 800);
                    $('.is-draggable[data-locator=locator-group-B]').css('height', 800);


                    // Give the leaf elements some height to mimic actual components. Otherwise
                    // drag and drop fails as the elements on bunched on top of each other.
                    $('.level-element').css('height', 200);

                    return requests;
                };

                getComponent = function(locator) {
                    return containerView.$('.studio-xblock-wrapper[data-locator="' + locator + '"]');
                };

                getDragHandle = function(locator) {
                    var component = getComponent(locator);
                    return $(component.find('.drag-handle')[0]);
                };

                dragComponentVertically = function (locator, dy) {
                    var handle = getDragHandle(locator);
                    handle.simulate("drag", {dy: dy});
                };

                dragComponentAbove = function (sourceLocator, targetLocator) {
                    var targetElement = getComponent(targetLocator),
                        targetTop = targetElement.offset().top + 1,
                        handle = getDragHandle(sourceLocator),
                        handleY = handle.offset().top + (handle.height() / 2),
                        dy = targetTop - handleY;
                    handle.simulate("drag", {dy: dy});
                };

                verifyRequest = function (requests, reorderCallIndex, expectedURL, expectedChildren) {
                    var actualIndex, request, children, i;
                    // 0th call is the response to the initial render call to get HTML.
                    actualIndex = reorderCallIndex + 1;
                    expect(requests.length).toBeGreaterThan(actualIndex);
                    request = requests[actualIndex];
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
                    var actualIndex;
                    // Number of calls will be 1 more than expected because of the initial render call to get HTML.
                    actualIndex = reorderCallIndex + 1;
                    expect(requests.length).toBeGreaterThan(actualIndex);
                    requests[actualIndex].respond(status);
                };

                it('does nothing if item not moved far enough', function () {
                    var requests = init(this);
                    // Drag the first component in Group A down very slightly but not enough to move it.
                    dragComponentVertically(groupAComponent1, 5);
                    verifyNumReorderCalls(requests, 0);
                });

                it('can reorder within a group', function () {
                    var requests = init(this);
                    // Drag the third component in Group A to be the first
                    dragComponentAbove(groupAComponent3, groupAComponent1);
                    respondToRequest(requests, 0, 200);
                    verifyRequest(requests, 0, groupAUrl, [groupAComponent3, groupAComponent1, groupAComponent2]);
                });

                it('can drag from one group to another', function () {
                    var requests = init(this);
                    // Drag the first component in Group B to the top of group A.
                    dragComponentAbove(groupBComponent1, groupAComponent1);

                    // Respond to the two requests: add the component to Group A, then remove it from Group B.
                    respondToRequest(requests, 0, 200);
                    respondToRequest(requests, 1, 200);

                    verifyRequest(requests, 0, groupAUrl,
                        [groupBComponent1, groupAComponent1, groupAComponent2, groupAComponent3]);
                    verifyRequest(requests, 1, groupBUrl, [groupBComponent2, groupBComponent3]);
                });

                it('does not remove from old group if addition to new group fails', function () {
                    var requests = init(this);
                    // Drag the first component in Group B to the first group.
                    dragComponentAbove(groupBComponent1, groupAComponent1);
                    respondToRequest(requests, 0, 500);
                    // Send failure for addition to new group -- no removal event should be received.
                    verifyRequest(requests, 0, groupAUrl,
                        [groupBComponent1, groupAComponent1, groupAComponent2, groupAComponent3]);
                    // Verify that a second request was not issued
                    verifyNumReorderCalls(requests, 1);
                });

                it('can swap group A and group B', function () {
                    var requests = init(this);
                    // Drag Group B before group A.
                    dragComponentAbove(groupB, groupA);
                    respondToRequest(requests, 0, 200);
                    verifyRequest(requests, 0, containerTestUrl, [groupB, groupA]);
                });

                describe("Shows a saving message", function () {
                    it('hides saving message upon success', function () {
                        var requests, savingOptions;
                        requests = init(this);

                        // Drag the first component in Group B to the first group.
                        dragComponentAbove(groupBComponent1, groupAComponent1);
                        EditHelpers.verifyNotificationShowing(notificationSpy, 'Saving');
                        respondToRequest(requests, 0, 200);
                        EditHelpers.verifyNotificationShowing(notificationSpy, 'Saving');
                        respondToRequest(requests, 1, 200);
                        EditHelpers.verifyNotificationHidden(notificationSpy);
                    });

                    it('does not hide saving message if failure', function () {
                        var requests = init(this);

                        // Drag the first component in Group B to the first group.
                        dragComponentAbove(groupBComponent1, groupAComponent1);
                        EditHelpers.verifyNotificationShowing(notificationSpy, 'Saving');
                        respondToRequest(requests, 0, 500);
                        EditHelpers.verifyNotificationShowing(notificationSpy, 'Saving');

                        // Since the first reorder call failed, the removal will not be called.
                        verifyNumReorderCalls(requests, 1);
                    });
                });
            });
        });
    });

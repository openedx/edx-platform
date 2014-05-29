(function (require) {
'use strict';
require(
['video/10_grader_collection.js'],
function (GraderCollection) {
describe('VideoGraderCollection', function () {
    var state, graderCollection;

    beforeEach(function () {
        state = {
            el: $('.video'),
            videoPlayer: {
                duration: jasmine.createSpy().andReturn(100)
            },
            config: {
                hasScore: true,
                graders: {
                    scored_on_end: {isScored: false, graderValue: true},
                    scored_on_percent: {isScored: false, graderValue: 1}
                }
            }
        };
    });

    it('returns list of available graders on initialization', function () {
        var list = new GraderCollection(state.el, state);

        expect(list.length).toBe(2);
    });

    it('returns an empty list if module is not scoreable', function () {
        var list;

        state.config.hasScore = false;
        list = new GraderCollection(state.el, state);
        expect(list.length).toBe(0);
    });

    it('returns just a list of available graders', function () {
        var list;

        state.config.graders['bad_grader'] = function(){};
        list = new GraderCollection(state.el, state);
        expect(list.length).toBe(2);
    });

    it('returns just a list of unscored graders', function () {
        var list;

        state.config.graders.scored_on_end.isScored = true;
        list = new GraderCollection(state.el, state);
        expect(list.length).toBe(1);
    });
});
});
}(RequireJS.require));

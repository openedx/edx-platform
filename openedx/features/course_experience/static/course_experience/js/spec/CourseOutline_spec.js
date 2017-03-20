import * as constants from "edx-ui-toolkit/js/utils/constants";
import log from 'logger';
import { CourseOutline } from "../CourseOutline";

describe('Course outline factory', () => {
  describe('keyboard listener', () => {
    const triggerKeyListener = (current, destination, keyCode) => {
      current.focus();
      spyOn(destination, 'focus');

      $('.block-tree').trigger(
        $.Event('keydown', {
          keyCode,
          target: current,
        }),
      );
    };

    beforeEach(() => {
      loadFixtures('course_experience/fixtures/course-outline-fragment.html');
      new CourseOutline('.block-tree');
    });

    describe('when the down arrow is pressed', () => {
      it('moves focus from a subsection to the next subsection in the outline', () => {
        const current = $('a.focusable:contains("Homework - Labs and Demos")')[0];
        const destination = $('a.focusable:contains("Homework - Essays")')[0];

        triggerKeyListener(current, destination, constants.keyCodes.down);

        expect(destination.focus).toHaveBeenCalled();
      });

      it('moves focus to the section list if at a section boundary', () => {
        const current = $('li.focusable:contains("Example Week 3: Be Social")')[0];
        const destination = $('ol.focusable:contains("Lesson 3 - Be Social")')[0];

        triggerKeyListener(current, destination, constants.keyCodes.down);

        expect(destination.focus).toHaveBeenCalled();
      });

      it('moves focus to the next section if on the last subsection', () => {
        const current = $('a.focusable:contains("Homework - Essays")')[0];
        const destination = $('li.focusable:contains("Example Week 3: Be Social")')[0];

        triggerKeyListener(current, destination, constants.keyCodes.down);

        expect(destination.focus).toHaveBeenCalled();
      });
    });

    describe('when the up arrow is pressed', () => {
      it('moves focus from a subsection to the previous subsection in the outline', () => {
        const current = $('a.focusable:contains("Homework - Essays")')[0];
        const destination = $('a.focusable:contains("Homework - Labs and Demos")')[0];

        triggerKeyListener(current, destination, constants.keyCodes.up);

        expect(destination.focus).toHaveBeenCalled();
      });

      it('moves focus to the section group if at the first subsection', () => {
        const current = $('a.focusable:contains("Lesson 3 - Be Social")')[0];
        const destination = $('ol.focusable:contains("Lesson 3 - Be Social")')[0];

        triggerKeyListener(current, destination, constants.keyCodes.up);

        expect(destination.focus).toHaveBeenCalled();
      });

      it('moves focus last subsection of the previous section if at a section boundary', () => {
        const current = $('li.focusable:contains("Example Week 3: Be Social")')[0];
        const destination = $('a.focusable:contains("Homework - Essays")')[0];

        triggerKeyListener(current, destination, constants.keyCodes.up);

        expect(destination.focus).toHaveBeenCalled();
      });
    });
  });

  describe("eventing", function() {
    beforeEach(function() {
      loadFixtures("course_experience/fixtures/course-outline-fragment.html");
      CourseOutlineFactory(".block-tree");
      spyOn(Logger, "log");
    });

    it("sends an event when an outline section is clicked", function() {
      $('a.focusable:contains("Homework - Labs and Demos")').click();

      expect(Logger.log).toHaveBeenCalledWith("edx.ui.lms.link_clicked", {
        target_url: (
          window.location.origin +
            "/courses/course-v1:edX+DemoX+Demo_Course/jump_to/block-v1:edX+DemoX+Demo_Course+type" +
            "@sequential+block@graded_simulations"
        ),
        current_url: window.location.toString()
      });
    });
  });

});

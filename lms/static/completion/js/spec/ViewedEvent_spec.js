import { ElementViewing, ViewedEventTracker } from '../ViewedEvent';

describe('ViewedTracker', () => {
    let existingHTML;
    beforeEach(() => {
        existingHTML = document.body.innerHTML;
    });

    afterEach(() => {
        document.body.innerHTML = existingHTML;
    });

    it('calls the handlers when an element is viewed', () => {
        document.body.innerHTML = '<div id="d1"></div><div id="d2"></div><div id="d3"></div>';
        const tracker = new ViewedEventTracker();
        // eslint-disable-next-line no-restricted-syntax
        for (const element of document.getElementsByTagName('div')) {
            tracker.addElement(element, 1000);
        }
        // eslint-disable-next-line no-undef
        const handlerSpy = jasmine.createSpy('handlerSpy');
        tracker.addHandler(handlerSpy);
        const elvIter = tracker.elementViewings.values();
        // Pick two elements, and mock them so that one has met the criteria to be viewed,
        // and the other hasn't.
        const viewed = elvIter.next().value;
        // eslint-disable-next-line no-undef
        spyOn(viewed, 'areViewedCriteriaMet').and.returnValue(true);
        viewed.checkIfViewed();
        expect(handlerSpy).toHaveBeenCalledWith(viewed.el, {
            elementHasBeenViewed: true,
        });
        const unviewed = elvIter.next().value;
        // eslint-disable-next-line no-undef
        spyOn(unviewed, 'areViewedCriteriaMet').and.returnValue(false);
        unviewed.checkIfViewed();
        // eslint-disable-next-line no-undef
        expect(handlerSpy).not.toHaveBeenCalledWith(unviewed.el, jasmine.anything());
    });
});

describe('ElementViewing', () => {
    beforeEach(() => {
        // eslint-disable-next-line no-undef
        jasmine.clock().install();
    });

    afterEach(() => {
        // eslint-disable-next-line no-undef
        jasmine.clock().uninstall();
    });

    it('calls checkIfViewed when enough time has elapsed', () => {
        const viewing = new ElementViewing({}, 500, () => {});
        // eslint-disable-next-line no-undef
        spyOn(viewing, 'checkIfViewed').and.callThrough();
        viewing.seenForMs = 250;
        viewing.handleVisible();
        // eslint-disable-next-line no-undef
        jasmine.clock().tick(249);
        expect(viewing.checkIfViewed).not.toHaveBeenCalled();
        // eslint-disable-next-line no-undef
        jasmine.clock().tick(1);
        expect(viewing.checkIfViewed).toHaveBeenCalled();
    });

    it('has been viewed after the specified number of milliseconds', () => {
        const viewing = new ElementViewing({}, 500, () => {});
        viewing.seenForMs = 250;
        // eslint-disable-next-line no-undef
        spyOn(Date, 'now').and.returnValue(750);
        viewing.handleVisible();
        viewing.markTopSeen();
        viewing.markBottomSeen();
        Date.now.and.returnValue(999);
        viewing.checkIfViewed();
        expect(viewing.hasBeenViewed).toBeFalsy();
        Date.now.and.returnValue(1000);
        // eslint-disable-next-line no-undef
        jasmine.clock().tick(250);
        expect(viewing.hasBeenViewed).toBeTruthy();
    });

    it('has not been viewed if the bottom has not been seen', () => {
        const viewing = new ElementViewing(undefined, 500, () => {});
        viewing.markTopSeen();
        viewing.seenForMs = 500;
        expect(viewing.areViewedCriteriaMet()).toBeFalsy();
        viewing.checkIfViewed();
        expect(viewing.hasBeenViewed).toBeFalsy();
    });

    it('has not been viewed if the top has not been seen', () => {
        const viewing = new ElementViewing(undefined, 500, () => {});
        viewing.markBottomSeen();
        viewing.seenForMs = 500;
        expect(viewing.areViewedCriteriaMet()).toBeFalsy();
        viewing.checkIfViewed();
        expect(viewing.hasBeenViewed).toBeFalsy();
    });

    it('does not update time seen if lastSeen is undefined', () => {
        const viewing = new ElementViewing(undefined, 500, () => {});
        viewing.becameVisibleAt = undefined;
        expect(viewing.becameVisibleAt).toBeUndefined();
        viewing.handleVisible();
        expect(viewing.becameVisibleAt).not.toBeUndefined();
    });
});

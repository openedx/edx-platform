describe('interpolate_ntext', function() {
    it('replaces placeholder values', function() {
        // eslint-disable-next-line no-undef
        expect(interpolate_ntext('contains {count} student', 'contains {count} students', 1, {count: 1}))
            .toBe('contains 1 student');
        // eslint-disable-next-line no-undef
        expect(interpolate_ntext('contains {count} student', 'contains {count} students', 5, {count: 2}))
            .toBe('contains 2 students');
    });
});

describe('interpolate_text', function() {
    it('replaces placeholder values', function() {
        // eslint-disable-next-line no-undef
        expect(interpolate_text('contains {adjective} students', {adjective: 'awesome'}))
            .toBe('contains awesome students');
    });
});

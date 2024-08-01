module.exports = {
    extends: '@edx/stylelint-config-edx',
    rules: {
        'selector-anb-no-unmatchable': null, // Disable the unknown rule
        'no-descending-specificity': null
    }
};

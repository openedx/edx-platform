module.exports = {
    extends: '@edx/eslint-config',
    root: true,
    settings: {
        'import/resolver': {
            webpack: {
                config: 'webpack.dev.config.js',
            },
        },
    },
    rules: {
        'import/prefer-default-export': 'off',
        indent: ['error', 4],
        'import/extensions': 'off',
        'import/no-unresolved': 'off',
        'react/jsx-indent': 'off',
        'react/jsx-indent-props': 'off',
    },
};

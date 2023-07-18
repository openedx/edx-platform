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
        indent: ['error', 4],
        'react/jsx-indent': ['error', 4],
        'react/jsx-indent-props': ['error', 4],
        'import/extensions': 'off',
        'import/no-unresolved': 'off',
    },
};

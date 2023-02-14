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
};

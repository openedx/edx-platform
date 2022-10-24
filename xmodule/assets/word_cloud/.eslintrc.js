module.exports = {
  extends: '@edx/eslint-config',
  root: true,
  settings: {
    'import/resolver': 'webpack',
  },
  overrides: {
    excludedFiles: 'public/js/*',
  },
};

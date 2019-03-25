module.exports = {
  extends: 'eslint-config-edx',
  root: true,
  settings: {
    'import/resolver': 'webpack',
  },
  overrides: {
    excludedFiles: 'public/js/*',
  },
};

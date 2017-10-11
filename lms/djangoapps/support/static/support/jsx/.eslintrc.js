module.exports = {
  extends: 'eslint-config-edx',
  root: true,
  settings: {
    'import/resolver': 'webpack',
  },
  rules: {
    'import/prefer-default-export': 'off',
  },
};

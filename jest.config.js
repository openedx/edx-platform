module.exports = {
    "globals": {
        "gettext": (t) => { return t; },
    },
    "modulePaths": [
        "common/static/common/js/components",
    ],
    "setupFilesAfterEnv": ["<rootDir>/setupTests.js"],
    "testMatch": [
        "/**/*.test.jsx",
        "common/static/common/js/components/**/?(*.)+(spec|test).js?(x)",
    ],
    "testEnvironment": "jsdom",
    "transform": {
        "^.+\\.jsx$": "babel-jest",
        "^.+\\.js$": "babel-jest",
    },
};

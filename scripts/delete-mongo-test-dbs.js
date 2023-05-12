/*
Drop all Mongo test databases.

Usage example:

    mongo delete-mongo-test-dbs.js

will drop every database that starts with "test_" or "acceptance_",
but ignore other databases.
*/

// eslint-disable-next-line no-extend-native
String.prototype.startsWith = function(substring) {
    return (this.indexOf(substring) === 0);
};

/* eslint-disable-next-line no-undef, no-var */
var dbNameList = db.getMongo().getDBNames();
/* eslint-disable-next-line no-var, no-restricted-syntax */
for (var i in dbNameList) {
    if (dbNameList[i].startsWith('test_') || dbNameList[i].startsWith('acceptance_')) {
        // eslint-disable-next-line no-undef
        dbToDrop = db.getMongo().getDB(dbNameList[i]);
        // eslint-disable-next-line no-restricted-globals
        print('Dropping test db ' + dbNameList[i]);
        // eslint-disable-next-line no-undef
        dbToDrop.dropDatabase();
    }
}

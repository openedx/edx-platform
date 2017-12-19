#!/bin/bash

# Upgrade the version of pysqlite/sqlite to avoid crashes during testing.
# Ideally, this code would just install a pre-built wheel - change it to this
# once edX has its own artifact server.
pip uninstall -y pysqlite
rm -rf tmp_pysqlite_upgrade && mkdir -p tmp_pysqlite_upgrade && cd tmp_pysqlite_upgrade
curl -o 2.8.3.tar.gz https://codeload.github.com/ghaering/pysqlite/tar.gz/2.8.3
curl -o sqlite-autoconf-3140100.tar.gz https://www.sqlite.org/2016/sqlite-autoconf-3140100.tar.gz
tar -xzvf sqlite-autoconf-3140100.tar.gz
tar -xzvf 2.8.3.tar.gz
cp -av sqlite-autoconf-3140100/. pysqlite-2.8.3/
cd ./pysqlite-2.8.3 && python setup.py build_static install
cd ../.. && rm -rf tmp_pysqlite_upgrade

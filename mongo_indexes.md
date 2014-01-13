These are the indexes each mongo db should have in order to perform well.
Each section states the collection name and then the indexes. To create an index,
you'll typically either use the mongohq type web interface or a standard terminal console.
If a terminal, this assumes you've logged in and gotten to the mongo prompt 
```
mongo mydatabasename
```

If using the terminal, to add an index to a collection, you'll need to prefix ```ensureIndex``` with
```
db.collection_name
```
as in ```db.location_map.ensureIndex({'course_id': 1}{background: true})```

location_map:
=============

```
ensureIndex({'_id.org': 1, '_id.course': 1})
ensureIndex({'course_id': 1})
```

fs.files:
=========

```
ensureIndex({'displayname': 1})
```

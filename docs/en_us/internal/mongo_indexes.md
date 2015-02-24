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

fs.files:
=========

Index needed thru 'category' by `_get_all_content_for_course` and others. That query also takes a sort
which can be `uploadDate`, `display_name`, 

Replace existing index which leaves out `run` with this one:
```
ensureIndex({'_id.org': 1, '_id.course': 1, '_id.name': 1}, {'sparse': true})
ensureIndex({'content_son.org': 1, 'content_son.course': 1, 'content_son.name': 1}, {'sparse': true})
ensureIndex({'_id.org': 1, '_id.course': 1, 'uploadDate': 1}, {'sparse': true})
ensureIndex({'_id.org': 1, '_id.course': 1, 'display_name': 1}, {'sparse': true})
ensureIndex({'content_son.org': 1, 'content_son.course': 1, 'uploadDate': 1}, {'sparse': true})
ensureIndex({'content_son.org': 1, 'content_son.course': 1, 'display_name': 1}, {'sparse': true})
```

modulestore:
============

Mongo automatically indexes the ```_id``` field but as a whole. Thus, for queries against modulestore such
as ```modulestore.find({'_id': {'tag': 'i4x', 'org': 'myu', 'course': 'mycourse', 'category': 'problem', 'name': '221abc', 'revision': null}})```
where every field in the id is given in the same order as the field is stored in the record in the db
and no field is omitted.

Because we often query for some subset of the id, we define this index:

```
ensureIndex({'_id.org': 1, '_id.course': 1, '_id.category': 1, '_id.name': 1})
```

Because we often scan for all category='course' regardless of the value of the other fields:
```
ensureIndex({'_id.category': 1})
```

Because lms calls get_parent_locations frequently (for path generation):
```
ensureIndex({'definition.children': 1}, {'sparse': true})
```

modulestore.active_versions
===========================

```
ensureIndex({'org': 1, 'course': 1, 'run': 1}, {'unique': true})
```

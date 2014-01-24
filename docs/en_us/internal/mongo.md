# Notes on using mongodb backed LMS and CMS

These are some random notes for developers, on how things are stored in mongodb, and how to debug mongodb data.

## Databases

Two mongodb databases are used:

- xmodule: stores module definitions and metadata (modulestore)
- xcontent: stores filesystem content, like PDF files

modulestore documents are stored with an _id which has fields like this:

    {"_id": {"tag":"i4x","org":"HarvardX","course":"CS50x","category":"chapter","name":"Week_1","revision":null}}

## Document fields

### Problems

Here is an example showing the fields available in problem documents:

    {
	"_id" : {
		"tag" : "i4x",
		"org" : "MITx",
		"course" : "6.00x",
		"category" : "problem",
		"name" : "ps03:ps03-Hangman_part_2_The_Game",
		"revision" : null
	},
	"definition" : {
		"data" : " ..."
	},
	"metadata" : {
		"display_name" : "Hangman Part 2: The Game",
		"attempts" : "30",
		"title" : "Hangman, Part 2",
		"data_dir" : "6.00x",
		"type" : "lecture"
	}
    }

## Sample interaction with mongodb

1. "mongo"
2. "use xmodule"
3. "show collections" should give "modulestore" and "system.indexes"
4. 'db.modulestore.find( {"_id.org": "MITx"} )' will produce a list of all MITx course documents
5. 'db.modulestore.find( {"_id.org": "MITx", "_id.category": "problem"} )' will produce a list of all problems in MITx courses

Example query for finding all files with "image" in the filename:

- use xcontent
- db.fs.files.find({'filename': /image/ } )
- db.fs.files.find({'filename': /image/ } ).count()

## Debugging the mongodb contents

A convenient tool is http://phpmoadmin.com/  (needs php)

Under ubuntu, do:

  - apt-get install php5-fpm php-pear
  - pecl install mongo
  - edit /etc/php5/fpm/php.ini to add "extension=mongo.so"
  - /etc/init.d/php5-fpm restart

and also setup nginx to run php through fastcgi.

## Backing up mongodb

- mogodump  (dumps all dbs)
- mongodump --collection modulestore --db xmodule (dumps just xmodule/modulestore)
- mongodump  -d xmodule -q '{"_id.org": "MITx"}' (dumps just MITx documents in xmodule)
- mongodump -q '{"_id.org": "MITx"}' (dumps all MITx documents)

## Deleting course content

Use "remove" instead of "find":

- db.modulestore.remove( {"_id.course": "8.01greytak"})

## Finding useful information from the mongodb modulestore

- Organizations

    > db.modulestore.distinct( "_id.org")
    [ "HarvardX", "MITx", "edX", "edx" ]

- Courses

    > db.modulestore.distinct( "_id.course")
    [
    	"CS50x",
    	"PH207x",
    	"3.091x",
    	"6.002x",
    	"6.00x",
    	"8.01esg",
    	"8.01rq_MW",
    	"8.02teal",
    	"8.02x",
    	"edx4edx",
    	"toy",
    	"templates"
    ]

- Find a problem which has the word "quantum" in its definition

    db.modulestore.findOne( {"definition.data":/quantum/})n

- Find Location for all problems with the word "quantum" in its definition

    db.modulestore.find( {"definition.data":/quantum/}, {'_id':1})

- Number of problems in each course

    db.runCommand({
      mapreduce: "modulestore",
      query: { '_id.category': 'problem' },
      map: function(){ emit(this._id.course, {count:1}); },
      reduce: function(key, values){
                  var result = {count:0};
     	      values.forEach(function(value) {
    	          result.count += value.count;
    	      });
    	      return result;
    	   },
      out: 'pbyc',
      verbose: true
    });

    produces:

    > db.pbyc.find()
    { "_id" : "3.091x", "value" : { "count" : 184 } }
    { "_id" : "6.002x", "value" : { "count" : 176 } }
    { "_id" : "6.00x", "value" : { "count" : 147 } }
    { "_id" : "8.01esg", "value" : { "count" : 184 } }
    { "_id" : "8.01rq_MW", "value" : { "count" : 73 } }
    { "_id" : "8.02teal", "value" : { "count" : 5 } }
    { "_id" : "8.02x", "value" : { "count" : 99 } }
    { "_id" : "PH207x", "value" : { "count" : 25 } }
    { "_id" : "edx4edx", "value" : { "count" : 50 } }
    { "_id" : "templates", "value" : { "count" : 11 } }

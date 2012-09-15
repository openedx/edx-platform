# Running the discussion service

## Instruction for Mac

## Installing Mongodb

If you haven't done so already:

    brew install mongodb

Make sure that you have mongodb running. You can simply open a new terminal tab and type:

    mongod

## Installing elasticsearch

    brew install elasticsearch

For debugging, it's often more convenient to have elasticsearch running in a terminal tab instead of in background. To do so, simply open a new terminal tab and then type:

    elasticsearch -f

## Setting up the discussion service

First, make sure that you have access to the [github repository](https://github.com/rll/cs_comments_service). If this were not the case, send an email to dementrock@gmail.com.

First go into the mitx_all directory. Then type

    git clone git@github.com:rll/cs_comments_service.git
    cd cs_comments_service/

If you see a prompt asking "Do you wish to trust this .rvmrc file?", type "y"

Now if you see this error "Gemset 'cs_comments_service' does not exist," run the following command to create the gemset and then use the rvm environment manually:

    rvm gemset create 'cs_comments_service'
    rvm use 1.9.3@cs_comments_service

Now use the following command to install required packages:

    bundle install

The following command creates database indexes:

    bundle exec rake db:init

Now use the following command to generate seeds (basically some random comments in Latin):

    bundle exec rake db:seed

It's done! Launch the app now:

    ruby app.rb

## Running the delayed job worker

In the discussion service, notifications are handled asynchronously using a third party gem called delayed_job. If you want to test this functionality, run the following command in a separate tab:

    bundle exec rake jobs:work

## Initialize roles and permissions

To fully test the discussion forum, you might want to act as a moderator or an administrator. Currently, moderators can manage everything in the forum, and administrator can manage everything plus assigning and revoking moderator status of other users.

First make sure that the database is up-to-date:

    rake django-admin[syncdb]
    rake django-admin[migrate]

For convenience, add the following environment variables to the terminal (assuming that you're using configuration set lms.envs.dev):

    export DJANGO_SETTINGS_MODULE=lms.envs.dev
    export PYTHONPATH=.

Now initialzie roles and permissions, providing a course id eg.:

    django-admin.py seed_permissions_roles "MITx/6.002x/2012_Fall"

To assign yourself as a moderator, use the following command (assuming your username is "test", and the course id is "MITx/6.002x/2012_Fall"):

    django-admin.py assign_role test Moderator "MITx/6.002x/2012_Fall"

To assign yourself as an administrator, use the following command

    django-admin.py assign_role test Administrator "MITx/6.002x/2012_Fall"

## Some other useful commands

### generate seeds for a specific forum
The seed generating command above assumes that you have the following discussion tags somewhere in the course data:

    <discussion for="Welcome Video" id="video_1" discussion_category="Video"/>
    <discussion for="Lab 0: Using the Tools" id="lab_1" discussion_category="Lab"/>
    <discussion for="Lab Circuit Sandbox" id="lab_2" discussion_category="Lab"/>

For example, you can insert them into overview section as following:

    <chapter name="Overview">
      <section format="Video" name="Welcome">
        <vertical>
          <video youtube="0.75:izygArpw-Qo,1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8"/>
          <discussion for="Welcome Video" id="video_1" discussion_category="Video"/>
        </vertical>
      </section>
      <section format="Lecture Sequence" name="System Usage Sequence">
        <%include file="sections/introseq.xml"/>
      </section>
      <section format="Lab" name="Lab0: Using the tools">
        <vertical>
          <html> See the <a href="/section/labintro"> Lab Introduction </a> or <a href="/static/handouts/schematic_tutorial.pdf">Interactive Lab Usage Handout </a> for information on how to do the lab </html>
          <problem name="Lab 0: Using the Tools" filename="Lab0" rerandomize="false"/>
          <discussion for="Lab 0: Using the Tools" id="lab_1" discussion_category="Lab"/>
        </vertical>
      </section>
      <section format="Lab" name="Circuit Sandbox">
        <vertical>
          <problem name="Circuit Sandbox" filename="Lab_sandbox" rerandomize="false"/>
          <discussion for="Lab Circuit Sandbox" id="lab_2" discussion_category="Lab"/>
        </vertical>
      </section>
    </chapter>

Currently, only the attribute "id" is actually used, which identifies discussion forum. In the code for the data generator, the corresponding lines are:

    generate_comments_for("video_1")
    generate_comments_for("lab_1")
    generate_comments_for("lab_2")

We also have a command for generating comments within a forum with the specified id:

    bundle exec rake db:generate_comments[type_the_discussion_id_here]

For instance, if you want to generate comments for a new discussion tab named "lab_3", then use the following command

    bundle exec rake db:generate_comments[lab_3]

### Running tests for the service

    bundle exec rspec

Warning: the development and test environments share the same elasticsearch index. After running tests, search may not work in the development environment. You simply need to reindex:

    bundle exec rake db:reindex_search

### debugging the service

You can use the following command to launch a console within the service environment:

    bundle exec rake console

### show user roles and permissions

Use the following command to see the roles and permissions of a user in a given course (assuming, again, that the username is "test"):

    django-admin.py show_permissions moderator

You need to make sure that the environment variables are exported. Otherwise you would need to do

    django-admin.py show_permissions moderator --settings=lms.envs.dev --pythonpath=.

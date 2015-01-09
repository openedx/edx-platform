## Starting and checking the status of builds
There are three ways that builds start in our jenkins testing infastructure for edx-platform.  

##### 1) Automatically started builds for Pull Requests
* Permissions Required: You must be a _public_ member of the [edx organization on github](https://github.com/orgs/edx/people).
  If you are not, someone will start a build for you during the pull request review process. You will still be able to
  view the build results as described below.

* How it gets started  
  
  >* When you submit a pull request to the edx-platform repository, a jenkins build will
  >  automatically start and run unit and acceptance tests at the most recent commit.
  >* When you add a new commit to the PR, a new build will be run for those changes.
  >* Sometimes it may take a little while for the build to start. That usually just means that
  >  jenkins is pretty busy.

* How it is reported  
  
  >* You will know a build is started if you see this:  
  >
  >  ![Running Tests](jenkins_images/started_tests.png)
  >
  >* When it is finished you will see either a green checkmark or a red X, indicating that the
  >  build either passed or failed respectively.  
  >
  >  ![Passed Tests](jenkins_images/passed_tests.png) 
  >
  >  ![Failed Tests](jenkins_images/failed_tests.png)  
  >* You can click on 'details' to take you to the jenkins build report.
    

##### 2) Manually started builds for commits or pull requests

* Permissions Required: You must be a _public_ member of the [edx organization on github](https://github.com/orgs/edx/people).

* How it gets started
  
  >1. Go to [https://build.testeng.edx.org/job/edx-platform-all-tests/build](https://build.testeng.edx.org/job/edx-platform-all-tests/build)
  >2. Make sure you are __logged in__. If you are already logged in, your username and a 'log out' link will be in the
  >   upper right corner of the page. Else, the 'log in' link will be there.
  >4. Enter either the commit hash or the pull request refspec that you want to test. Examples of valid refspecs are below the input field.
  >5. Click 'Build'.
  
* How it is reported
  
  >* When you start the build, it will redirect you to the log page.  You can watch this page for
  >  results. 
  >* The results will also be reported to github, and will show up next to your commit on a PR or
  >  other places that the commit is listed (search results, etc.). 
  >* If you started the build using a pull request refspec or the most recent commit hash on an open pull request, then it will be reported the same as automatic builds for pull requests. (See point 1 of this page.)

##### 3) Automatically started builds for new commits to the 'master' branch
* A build is started whenever there is a new commit on the 'master' branch.
* To see recent builds of 'master' look at the [edx-platform-all-tests-master](https://build.testeng.edx.org/job/edx-platform-all-tests-master/) job

var data_m = [
  {
  title: gettext('To know more about courses'),
  answer: gettext('Click the course to view the course introduction video, browse the course introduction, instructor introduction and course outline, etc.')
  },{
  title: gettext('To join as a member'), 
  answer: gettext('Enter "Membership" page, choose your learning duration and payment method. After payment is completed, you can enjoy learning all courses on EliteMBA during the study period.'),
  },{
  title: gettext('To view the end-date of membership'), 
  answer: gettext('Enter "Membership" page to view the VIP open date and remaining days.'),
  },{
  title: gettext('To enroll as a member'), 
  answer: gettext('Enter "Discover New" page, click the course or search key words to select courses you are interested in, click "Free Enrollment for VIP" button, then the enrollment is fulfilled.'),
  },{
  title: gettext('To purchase a course'), 
  answer: gettext('Enter "Discover New" page, click the course or search key words to select courses you are interested in, click "Enroll" button, then you can start learning after payment is completed.'),
  },{
  title: gettext('To start a course'), 
  answer: gettext('Click your avatar in the upper right corner of the page, enter "Dashboard" to view the course introduction, watch videos and complete assignments.'),
  },{
  title: gettext('To participate in discussion'),
  answer: gettext('Enter "Dashboard - View Course" page, click "Discussion". You can view discussions, engage with posts and receive updates.'),
  },{
  title: gettext('To view and download handouts'),
  answer: gettext('Enter "Dashboard - View Course" page, find "Course Handouts" on the right side. You can view handout content and download.')
  }
];
var tab = '';
var content = '';
var active = 0;
for (var i = 0; i < data_m.length; i++){
  tab = tab + '<div class="manual-tab" onclick="showBlock(' + i + ')">' + data_m[i].title + '</div>';
  content = content + '<div class="manual-block" style="display:none"><p class="ques-title">' + data_m[i].title + '</p>' + '<p class="ques-answer">' + data_m[i].answer + '</p></div>';
}
$('.manual-tabs')[0].innerHTML = tab;
$('.manual-content')[0].innerHTML = content;
$('.manual-block')[active].style.display = 'block';
$('.manual-tab')[active].classList.add('manual-tab-active');


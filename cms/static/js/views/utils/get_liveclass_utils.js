
/**
 * Provides utilities for validating liveclass during creation.
 */
 define(["jquery", "gettext", "common/js/components/utils/view_utils", "js/views/utils/create_utils_base"], function (
  $,
  gettext,
  ViewUtils,
  CreateUtilsFactory
) {
  "use strict";
  return function (selectors, classes) {
    var keyLengthViolationMessage = gettext(
      "The combined length of the organization and library code fields" +
        " cannot be more than <%- limit %> characters."
    );
    var keyFieldSelectors = [selectors.org, selectors.number];
    var nonEmptyCheckFieldSelectors = [selectors.name, selectors.org, selectors.number];

    CreateUtilsFactory.call(this, selectors, classes);

    var endpoint = "http://studio.launchpadlearning.ca/live_class/details/";
    var lib_info = {};

    //Pagination is implemented using the two buttons
    var nextButton = document.querySelector(".liveclass-next");
    var prevButton = document.querySelector(".liveclass-previous");
    var nextButtonPressed = () => {
      endpoint = nextButton.value;
      this.create(lib_info, function (res, errorMessage) {});
    };
    var prevButtonPressed = () => {
      endpoint = prevButton.value;
      this.create(lib_info, function (res, errorMessage) {});
    };

    //To Delete selected Live class
    var deleteLive = (e) => {
      let id = e.target.attributes.value.value;
      $.deleteJSON("http://studio.launchpadlearning.ca/live_class/" + id, id, function (id) {});
      window.location.reload();
    };

    //To Update Live class
    var updateLive = (e) => {
      let id = e.target.attributes.value.value;
      var createLiveButton = document.querySelector(".new-liveclass-button");
      createLiveButton.click();
      console.log(id);

      //Getting details of Live class using id
      $.getJSON("http://studio.launchpadlearning.ca/live_class/" + id, id, function (id) {}).then((data) => {
        console.log(data);

        displayAssignedUsers(data.id);

        var $newLiveClassForm = $("#create-liveclass-form");
        // var course_name = $newLiveClassForm.find("#category").val(data.course.course_name);
        console.log(data.course.course_name);
        document.querySelector("#category").disabled = true;
        document.querySelector("#category").value = data.course.course_name;

        var topic_name = $newLiveClassForm.find("#new-liveclass-name").val(data.topic_name);
        var meetings_notes = $newLiveClassForm.find("#new-liveclass-notes").val(data.meeting_notes);
        var is_recurrence_meeting = $newLiveClassForm
          .find("#field-liveclass-recurrence")
          .val(data.is_recurrence_meeting);
        var start_date = $newLiveClassForm.find("#new-liveclass-startdate").val(data.start_date);
        var end_date = $newLiveClassForm.find("#new-liveclass-enddate").val(data.end_date);
        var start_time = $newLiveClassForm.find("#new-liveclass-starttime").val(data.start_time);
        var end_time = $newLiveClassForm.find("#new-liveclass-endtime").val(data.end_time);
        $newLiveClassForm.find(".liveclass-title").text("Update Live Class");

        //Replacing Create button with Update button
        var updateButton = document.createElement("input");
        $newLiveClassForm.find(".new-liveclass-save").replaceWith(updateButton);
        updateButton.classList.add("action", "action-primary", "updateLiveClass");
        updateButton.type = "button";
        updateButton.value = "Update";
        updateButton.innerText = "Update";

        localStorage.setItem("liveclass_id", data.id);
        console.log(localStorage.getItem("liveclass_id"));

        updateButton.onclick = () => {
          var lib_info = {
            course_id: data.course.course_id,
            course_name: data.course.course_name,
            topic_name: topic_name.val(),
            meeting_notes: meetings_notes.val(),
            is_recurrence_meeting: is_recurrence_meeting.val(),
            start_date: start_date.val(),
            end_date: end_date.val(),
            start_time: start_time.val(),
            end_time: end_time.val(),
          };

          //Validating Start and End
          if (
            start_date.val() < end_date.val() ||
            (start_date.val() === end_date.val() && start_time.val() < end_time.val())
          ) {
            $.patchJSON("http://studio.launchpadlearning.ca/live_class/" + id, lib_info, function (id) {}).then(() => {
              console.log("Update Success");
              window.location.reload();
            });
          } else {
            alert("Ending should be after Starting");
          }
        };
      });
    };

    var displayAssignedUsers = (id) => {
      $.getJSON("http://studio.launchpadlearning.ca/live_class/enroll/detail/" + id, {}).then((data) => {
        var assignedUsersList = document.querySelector(".assigned-liveclass-users");
        assignedUsersList.innerText = "";
        if (data.results.length !== 0) {
          data.results.forEach((user) => {
            var assignedUser = document.createElement("li");
            assignedUser.key = user.id;
            assignedUser.innerText = user.user.username;
            assignedUsersList.appendChild(assignedUser);
          });
        }else{
          assignedUsersList.innerText = "No Users Assigned";
          console.log("No assigned users");
        }
      });
    };

    this.create = function (liveclassInfo, errorHandler) {
      $.getJSON(endpoint, liveclassInfo)
        .done(function (response) {
          var output = document.getElementById("output");
          output.innerHTML = "";
          output.style.display = "block";

          var outputButtons = document.createElement("div");
          outputButtons.id = "output-buttons";
          outputButtons.style = "width:100%"

          var nextButton = document.createElement("input");
          nextButton.type = "button";
          nextButton.innerText = "Next";
          nextButton.className = "liveclass-next"

          var prevButton = document.createElement("input");
          prevButton.type = "button";
          prevButton.innerText = "Previous";
          prevButton.className = "liveclass-previous"

          outputButtons.append(prevButton, nextButton);


          //Assigning the values of Previous and Next buttons
          response.next === null
            ? (nextButton.value = "http://studio.launchpadlearning.ca/live_class/details/")
            : (nextButton.value = response.next);
          response.previous === null
            ? (prevButton.value = "http://studio.launchpadlearning.ca/live_class/details/?page=" + response.num_pages)
            : (prevButton.value = response.previous);

          //Getting list of live classes as js object
          var response = JSON.parse(JSON.stringify(response.results));

          //Creating List of Live classes
          let live_list = document.createElement("ul");
          live_list.className = "list-courses";

          //Creating each item in the List, having Update and Delete Button
          response.forEach((item, i) => {
            let live_list_item = document.createElement("li");
            live_list_item.className = "course-item";
            //Adding details of each Live class
            live_list_item.innerHTML = `<a class="course-link" href=${item.meeting_link}?t=${item.client_token} key="${item.id}" >
                                        <h3 class="course-title">${item.topic_name}</h3>
                                        <div class="course-metadata">
                                            <span class="course-org metadata-item">
                                                <span class="label">${item.course.course_name}</span>
                                                <span class="value">${item.course.course_name}</span>
                                            </span>
                                        </div>
                                    </a>`;

            //Adding Buttons
            let live_list_buttons = document.createElement("ul");
            live_list_buttons.classList.add("item-actions", "course-actions");

            //Update Button
            let liveUpdate = document.createElement("li");
            liveUpdate.classList.add("action", "action-rerun");
            liveUpdate.innerHTML = `<a class="liveclass-update-button button rerun-button" value=${item.id} href="#">Update</a>`;
            liveUpdate.onclick = updateLive;
            live_list_buttons.appendChild(liveUpdate);

            //Delete Button
            let liveDelete = document.createElement("li");
            liveDelete.classList.add("action", "action-view");
            liveDelete.innerHTML = `<a class="liveclass-delete-button button rerun-button" value=${item.id} href="#">Delete</a>`;
            liveDelete.onclick = deleteLive;
            live_list_buttons.appendChild(liveDelete);

            live_list_item.appendChild(live_list_buttons);
            live_list.appendChild(live_list_item);
          });

          output.prepend(live_list);
          nextButton.onclick = nextButtonPressed;
          prevButton.onclick = prevButtonPressed;
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          var reason = errorThrown;
          if (jqXHR.responseText) {
            try {
              var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
              if (detailedReason) {
                reason = detailedReason;
              }
            } catch (e) {}
          }
          errorHandler(reason);
        });
    };

    this.getCourse = function (object, errorHandler) {
      $.getJSON("courses/all/courses ", object).done(function (response) {
        var catOptions = "";
        for (let i = 0; i < response.length; i++) {
          catOptions += "<option id=" + response[i]["id"] + ">" + response[i]["name"] + "</option>";

          document.getElementById("category").innerHTML = catOptions;
        }
      });
    };

    this.getUser = function (liveclassInfo, errorHandler) {
      $.getJSON("/accounts/details", liveclassInfo)
        .done(function (response) {
          errorHandler(response);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          var reason = errorThrown;
          if (jqXHR.responseText) {
            try {
              var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
              if (detailedReason) {
                reason = detailedReason;
              }
            } catch (e) {}
          }
          errorHandler(reason);
        });
    };

    this.assignUser = function (liveclassInfo, errorHandler) {
      $.postJSON("/live_class/user/enrollment", liveclassInfo)
        .done(function (response) {
          errorHandler(response);
        })
        .fail(function (jqXHR, textStatus, errorThrown) {
          var reason = errorThrown;
          if (jqXHR.responseText) {
            try {
              var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
              if (detailedReason) {
                reason = detailedReason;
              }
            } catch (e) {}
          }
          errorHandler(reason);
        });
    };
  };
});

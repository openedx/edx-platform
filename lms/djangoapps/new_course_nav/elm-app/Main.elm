module Main (..) where

import Effects exposing (Effects, Never)
import StartApp
import Task

import CourseNav
import ParseCourse exposing (getCourseBlocks)
import Types


init : (Types.CourseBlock, Effects Types.Action)
init =
  ( Types.Empty, getCourseBlocks courseBlocksApiUrl courseId )


app =
  StartApp.start
    { init = init
    , update = CourseNav.update
    , view = CourseNav.courseOutlineView
    , inputs = []
    }


main =
  app.html


-- ports
port courseId : String


port courseBlocksApiUrl : String


port tasks : Signal (Task.Task Never ())
port tasks =
  app.tasks

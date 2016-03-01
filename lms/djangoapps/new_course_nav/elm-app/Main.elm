module Main (..) where

import Effects exposing (Effects, Never)
import Hop
import StartApp
import Task

import CourseOutline
import ParseCourse exposing (getCourseBlocks)
import Types


-- Hop stuff
type Action
  = HopAction Hop.Action
  | ShowCourseOutline Hop.Payload
  | ShowBlock Hop.Payload
  | ShowNotFound Hop.Payload


routes : List (String, Hop.Payload -> Action)
routes =
  [ ("/", ShowCourseOutline)
  , ("/:blockId", ShowBlock)
  ]


init : (Types.CourseBlock, Effects Types.Action)
init =
  ( Types.Empty, getCourseBlocks courseBlocksApiUrl courseId )


app =
  StartApp.start
    { init = init
    , update = CourseOutline.update
    , view = CourseOutline.courseOutlineView
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

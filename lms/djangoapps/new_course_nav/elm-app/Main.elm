module Main (..) where

import Effects exposing (Effects, Never)
import Html exposing (..)
import Routing exposing (router)
import StartApp
import Task exposing (Task)

import CourseOutline
import ParseCourse exposing (getCourseBlocks)
import Types


type alias Model =
  { routing : Routing.Model
  , courseBlock : Types.CourseBlock
  }


-- TODO: refactor action types for clarity
type Action
  = RoutingAction Routing.Action
  | CourseBlocksAction Types.Action
  | NoOp


initialModel : Model
initialModel =
  { routing = Routing.initialModel
  , courseBlock = Types.Empty
  }


init : (Model, Effects Action)
init =
  -- ( initialModel, getCourseBlocks courseBlocksApiUrl courseId )
  ( initialModel
  , getCourseBlocks courseBlocksApiUrl courseId
      |> Effects.map CourseBlocksAction
  )


update : Action -> Model -> (Model, Effects Action)
update action model =
  case action of
    RoutingAction subAction ->
      let
        (updatedRouting, fx) = Routing.update subAction model.routing
        updatedModel = { model | routing = updatedRouting }
      in
        (updatedModel, Effects.map RoutingAction fx)

    CourseBlocksAction subAction ->
      let
        (updatedCourseBlock, fx) = CourseOutline.update subAction model.courseBlock
        updatedModel = { model | courseBlock = updatedCourseBlock }
      in
        (updatedModel, Effects.map CourseBlocksAction fx)

    _ ->
      (model, Effects.none)


view : Signal.Address Action -> Model -> Html
view address model =
  let
    childView =
      case model.routing.currentView of
        "courseOutline" ->
          CourseOutline.courseOutlineView
            (Signal.forwardTo address CourseBlocksAction)
            model.courseBlock

        _ ->
          text "oogabooga"
  in
    div [] [ childView ]


app =
  StartApp.start
    { init = init
    , update = update
    , view = view
    , inputs = [ Signal.map RoutingAction router.signal ]
    }


main =
  app.html


-- ports
port courseId : String


port courseBlocksApiUrl : String


port tasks : Signal (Task.Task Never ())
port tasks =
  app.tasks


port routeRunTask : Task () ()
port routeRunTask =
  router.run

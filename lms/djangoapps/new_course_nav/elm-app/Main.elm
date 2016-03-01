module Main (..) where

import Dict exposing (Dict)
import Effects exposing (Effects, Never)
import Html exposing (..)
import Html.Attributes exposing (..)
import Routing exposing (router)
import StartApp
import Task exposing (Task)

import CourseBlock
import CourseOutline
import ParseCourse exposing (getCourseBlocks)
import Styles
import Types


type alias Model =
  { routing : Routing.Model
  , courseBlock : Types.CourseBlock
  }


-- TODO: refactor action types for clarity
type Action
  = RoutingAction Routing.Action
  | CourseBlocksAction Types.CourseBlocksAction
  | CourseBlockAction CourseBlock.Action
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

    CourseBlockAction subaction ->
      (model, Effects.map CourseBlockAction Effects.none)

    NoOp ->
      (model, Effects.none)


view : Signal.Address Action -> Model -> Html
view address model =
  let
    childView =
      case model.routing.currentView of
        "courseOutline" ->
          CourseOutline.view
            (Signal.forwardTo address CourseBlocksAction)
            model.courseBlock

        "block" ->
          let
            blockId =
              model.routing.routerPayload.params
                |> Dict.get "blockId"
                |> Maybe.withDefault ""
          in
            CourseBlock.view
              (Signal.forwardTo address CourseBlockAction)
              blockId

        _ ->
          text ""
  in
    div
      [ class "grid-container grid-manual"
      , Styles.gridContainerStyle
      ]
      [ childView ]


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

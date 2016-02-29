module Main (..) where

import Effects exposing (Effects, Never)
import Debug
import Dict exposing (Dict)
import Html
import Html.Events
import Http
import Json.Decode exposing (..)
import Result
import StartApp
import Task


-- model
type alias URL =
  String


type alias CourseBlockAttributes =
  -- the course node identifier
  { id : String
  -- the type of the course node
  , nodeType : String
  -- the student-facing title of the course node
  , displayName : String
  -- LMS URL of the course node
  , lmsWebUrl : String
  -- -- API URL which renders the course node
  -- , studentViewUrl : String
  }


type CourseBlock
  = Empty
  | Course CourseBlockAttributes (List CourseBlock)
  | Chapter CourseBlockAttributes (List CourseBlock)
  | Sequential CourseBlockAttributes (List CourseBlock)
  | Vertical CourseBlockAttributes (List CourseBlock)
  | Leaf CourseBlockAttributes
  | Error


type alias CourseBlocksData =
  { root : String
  , blocks : Dict String CourseBlockData
  }


type alias CourseBlockData =
  { id : String
  , type' : String
  , display_name : String
  , lms_web_url : String
  , children : Maybe (List String)
  }


courseBlocksDecoder : Decoder CourseBlocksData
courseBlocksDecoder =
  object2 CourseBlocksData
    ("root" := string)
    ("blocks" := dict courseBlockDecoder)


courseBlockDecoder : Decoder CourseBlockData
courseBlockDecoder =
  object5 CourseBlockData
    ("id" := string)
    ("type" := string)
    ("display_name" := string)
    ("lms_web_url" := string)
    (maybe ("children" := list string))


fromApiResponse : CourseBlocksData -> CourseBlock
fromApiResponse response =
    let
      blah = Debug.log (toString response)
    in
      Error


-- update
type Action
  = CourseBlocksApiResponse (Result Http.Error CourseBlocksData)
  | CourseBlocksApiError Http.Error


update : Action -> CourseBlock -> (CourseBlock, Effects Action)
update action courseBlock =
  -- TODO: can we flatten the Ok/Err results into action types?
  let
    foo = Debug.log (toString action)
  in
    case action of
      CourseBlocksApiResponse result ->
        case result of
          Ok value ->
            -- TODO: handle failure value
            ( fromApiResponse value, Effects.none )

          Err value ->
            ( courseBlock, Effects.task (Task.succeed (CourseBlocksApiError value)) )

      CourseBlocksApiError value ->
        ( Error, Effects.none )


-- view
view : Signal.Address Action -> CourseBlock -> Html.Html
view address courseBlock =
  case courseBlock of
    Empty ->
      Html.text "Loading..."

    Course attributes children ->
      Html.text attributes.displayName

    Error ->
      Html.text "Error - Some sort of HTTP error occurred"

    _ ->
      Html.text "Error - expected a course."


-- app
init : (CourseBlock, Effects Action)
init =
  ( Empty, getCourseBlocks )


getCourseBlocks : Effects Action
getCourseBlocks =
  let
    url =
      Http.url
        courseBlocksApiUrl
        [ ( "course_id", courseId )
        , ( "all_blocks", "true" )
        , ( "depth", "all" )
        , ( "requested_fields", "children" )
        ]
  in
    Http.get courseBlocksDecoder url
      |> Task.toResult
      |> Task.map CourseBlocksApiResponse
      |> Effects.task


app =
  StartApp.start
    { init = init
    , update = update
    , view = view
    , inputs = []
    }


main =
  app.html


-- ports
port courseId : String


port courseApiUrl : URL


port courseBlocksApiUrl : URL


port tasks : Signal (Task.Task Never ())
port tasks =
  app.tasks

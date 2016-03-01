module ParseCourse (fromApiResponse, getCourseBlocks) where

import Dict exposing (Dict)
import Effects exposing (Effects)
import Http
import Json.Decode exposing (..)
import Task

import Types exposing (..)


getCourseBlocks : String -> String -> Effects Action
getCourseBlocks url courseId =
  let
    url =
      Http.url
        url
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
    ("student_view_url" := string)
    (maybe ("children" := list string))


fromApiResponse : CourseBlocksData -> CourseBlock
fromApiResponse courseBlocksData =
  buildCourseTree courseBlocksData courseBlocksData.root


buildCourseTree : CourseBlocksData -> String -> CourseBlock
buildCourseTree courseBlocksData rootId =
  if rootId == "" then
    Empty
  else
    let
      maybeBlockData = Dict.get rootId courseBlocksData.blocks
      blockData = Maybe.withDefault
        { id = ""
        , type' = ""
        , display_name = ""
        , student_view_url = ""
        , children = Just []
        }
        maybeBlockData
      blockAttributes =
        { id = blockData.id
        , nodeType = blockData.type'
        , displayName = blockData.display_name
        , studentViewUrl = blockData.student_view_url
        }
      children =
        List.map (buildCourseTree courseBlocksData) (Maybe.withDefault [] blockData.children)
    in
      if blockData.type' == "course" then
        Course blockAttributes children
      else if blockData.type' == "chapter" then
        Chapter blockAttributes children
      else if blockData.type' == "sequential" then
        Sequential blockAttributes children
      else if blockData.type' == "vertical" then
        Vertical blockAttributes children
      else
        Error

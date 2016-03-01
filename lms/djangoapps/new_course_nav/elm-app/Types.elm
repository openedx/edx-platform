module Types (..) where

import Dict exposing (Dict)
import Http


-- Defines all our actions within the app.
type Action
  = CourseBlocksApiResponse (Result Http.Error CourseBlocksData)
  | CourseBlocksApiSuccess CourseBlocksData
  | CourseBlocksApiError Http.Error


{-| CourseBlock and CourseBlockAttributes are the abstract types which represent
course structure within the app.
-}

-- Represents attributes on course blocks
type alias CourseBlockAttributes =
  { id : String
  , nodeType : String
  , displayName : String
  , lmsWebUrl : String
  }


-- Represents the course tree for the nav app
type CourseBlock
  = Empty
  | Course CourseBlockAttributes (List CourseBlock)
  | Chapter CourseBlockAttributes (List CourseBlock)
  | Sequential CourseBlockAttributes (List CourseBlock)
  | Vertical CourseBlockAttributes (List CourseBlock)
  | Leaf CourseBlockAttributes
  | Error


{-| CourseBlocksData and CourseBlockData represent the course data returned
from the Course Api.  They are intermediate data structures used during
parsing, but shouldn't be needed elsewhere.
-}

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

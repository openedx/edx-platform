module Styles (..) where

import Html exposing (..)
import Html.Attributes exposing (..)


gridContainerStyle : Attribute
gridContainerStyle =
  style
    [ ("padding", "30px") ]

btnBrandStyle : Attribute
btnBrandStyle =
    style
        [ ("margin-left", "10px")
        , ("box-shadow", "none")
        ]

chapterOutlineStyles : Attribute
chapterOutlineStyles =
    style
        [ ("margin-bottom", "30px") ]

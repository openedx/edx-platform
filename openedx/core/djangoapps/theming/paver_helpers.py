"""
This file contains helpers for paver commands, Django is not initialized in paver commands.
So, django settings, models etc. can not be used here.
"""
import os

from path import Path


def get_theme_paths(themes, theme_dirs):
    """
    get absolute path for all the given themes, if a theme is no found
    at multiple places than all paths for the theme will be included.
    If a theme is not found anywhere then theme will be skipped with
    an error message printed on the console.

    If themes is 'None' then all themes in given dirs are returned.

    Args:
        themes (list): list of all theme names
        theme_dirs (list): list of base dirs that contain themes
    Returns:
        list of absolute paths to themes.
    """
    theme_paths = []

    for theme in themes:
        theme_base_dirs = get_theme_base_dirs(theme, theme_dirs)
        if not theme_base_dirs:
            print(
                "\033[91m\nSkipping '{theme}': \n"
                "Theme ({theme}) not found in any of the theme dirs ({theme_dirs}). \033[00m".format(
                    theme=theme,
                    theme_dirs=", ".join(theme_dirs)
                ),
            )
        theme_paths.extend(theme_base_dirs)

    return theme_paths


def get_theme_base_dirs(theme, theme_dirs):
    """
    Get all base dirs where the given theme can be found.

    Args:
        theme (str): name of the theme to find
        theme_dirs (list): list of all base dirs where the given theme could be found

    Returns:
        list of all the dirs for the goven theme
    """
    theme_paths = []
    for _dir in theme_dirs:
        for dir_name in {theme}.intersection(os.listdir(_dir)):
            if is_theme_dir(Path(_dir) / dir_name):
                theme_paths.append(Path(_dir) / dir_name)
    return theme_paths


def is_theme_dir(_dir):
    """
    Returns true if given dir contains theme overrides.
    A theme dir must have subdirectory 'lms' or 'cms' or both.

    Args:
        _dir: directory path to check for a theme

    Returns:
        Returns true if given dir is a theme directory.
    """
    theme_sub_directories = {'lms', 'cms'}
    return bool(os.path.isdir(_dir) and theme_sub_directories.intersection(os.listdir(_dir)))

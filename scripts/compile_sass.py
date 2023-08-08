#!/usr/bin/env python
"""
Defines a CLI for compiling Sass (both default and themed) into CSS.

Should be run from the root of edx-platform using `npm run` wrapper.
Requirements for this scripts are stored in requirements/edx/assets.in.

Get more details:

     npm run compile-sass -- --help
     npm run compile-sass -- --dry

Setup (Tutor and Devstack will do this for you):

    python -m venv venv
    . venv/bin/activate
    pip install -r requirements/edx/assets.txt

Usage:

     npm run compile-sass             # prod, no args
     npm run compile-sass -- ARGS     # prod, with args
     npm run compile-sass-dev         # dev, no args
     npm run compile-sass-dev -- ARGS # dev, with args

This script is intentionally implemented in a very simplistic way. It prefers repetition
over abstraction, and its dependencies are minimal (just click and libsass-python, ideally).
We do this because:

* If and when we migrate from libsass-python to something less ancient like node-sass or dart-sass,
  we will want to re-write this script in Bash or JavaScript so that it can work without any
  backend tooling. By keeping the script dead simple, that will be easier.

* The features this script supports (legacy frontends & comprehensive theming) are on the way out,
  in favor of micro-frontends, branding, and Paragon design tokens. We're not sure how XBlock
  view styling will fit into that, but it probably can be much simpler than comprehensive theming.
  So, we don't need this script to be modular and extensible. We just need it to be obvious, robust,
  and easy to maintain until we can delete it.

See docs/decisions/0017-reimplement-asset-processing.rst for more details.
"""
from __future__ import annotations

import glob
import subprocess
from pathlib import Path

import click


# Accept both long- and short-forms of these words, but normalize to long form.
# We accept both because edx-platform asset build scripts historically use the short form,
# but NODE_ENV uses the long form, so to make them integrate more seamlessly we accept both.
NORMALIZED_ENVS = {
    "prod": "production",
    "dev": "development",
    "production": "production",
    "development": "development",
}


@click.option(
    "-T",
    "--theme-dir",
    "theme_dirs",
    metavar="PATH",
    multiple=True,
    envvar="EDX_PLATFORM_THEME_DIRS",
    type=click.Path(
        exists=True, file_okay=False, readable=True, writable=True, path_type=Path
    ),
    help=(
        "Consider sub-dirs of PATH as themes. "
        "Multiple theme dirs are accepted. "
        "If none are provided, we look at colon-separated paths on the EDX_PLATFORM_THEME_DIRS env var."
    ),
)
@click.option(
    "-t",
    "--theme",
    "themes",
    metavar="NAME",
    multiple=True,
    type=str,
    help=(
        "A theme to compile. "
        "NAME should be a sub-dir of a PATH provided by --theme-dir. "
        "Multiple themes are accepted. "
        "If none are provided, all available themes are compiled."
    ),
)
@click.option(
    "--skip-default",
    is_flag=True,
    help="Don't compile default Sass.",
)
@click.option(
    "--skip-themes",
    is_flag=True,
    help="Don't compile any themes (overrides --theme* options).",
)
@click.option(
    "--skip-lms",
    is_flag=True,
    help="Don't compile any LMS Sass.",
)
@click.option(
    "--skip-cms",
    is_flag=True,
    help="Don't compile any CMS Sass.",
)
@click.option(
    "--env",
    type=click.Choice(["dev", "development", "prod", "production"]),
    default="prod",
    help="Optimize CSS for this environment. Defaults to 'prod'.",
)
@click.option(
    "--dry",
    is_flag=True,
    help="Print what would be compiled, but don't compile it.",
)
@click.option(
    "-h",
    "--help",
    "show_help",
    is_flag=True,
    help="Print this help.",
)
@click.command()
@click.pass_context
def main(
    context: click.Context,
    theme_dirs: list[Path],
    themes: list[str],
    skip_default: bool,
    skip_themes: bool,
    skip_lms: bool,
    skip_cms: bool,
    env: str,
    dry: bool,
    show_help: bool,
) -> None:
    """
    Compile Sass for edx-platform and its themes.

    Default Sass is compiled unless explicitly skipped.
    Additionally, any number of themes may be specified using --theme-dir and --theme.

    Default CSS is compiled to css/ directories in edx-platform.
    Themed CSS is compiled to css/ directories in their source themes.
    """

    def compile_sass_dir(
        message: str,
        source: Path,
        dest: Path,
        includes: list[Path],
        tolerate_missing: bool = False,
    ) -> None:
        """
        Compile a directory of Sass into a target CSS directory, and generate any missing RTL CSS.

        Structure of source dir is mirrored in target dir.
        """
        use_dev_settings = NORMALIZED_ENVS[env] == "development"
        click.secho(f"  {message}...", fg="cyan")
        click.secho(f"      Source: {source}")
        click.secho(f"      Target: {dest}")
        if not source.is_dir():
            if tolerate_missing:
                click.secho(f"      Skipped because source directory does not exist.", fg="yellow")
                return
            else:
                raise FileNotFoundError(f"missing Sass source dir: {source}")
        click.echo(f"      Include paths:")
        for include in includes:
            click.echo(f"        {include}")
        if not dry:
            # Import sass late so that this script can be dry-run without installing
            # libsass, which takes a while as it must be compiled from its C source.
            import sass

            dest.mkdir(parents=True, exist_ok=True)
            sass.compile(
                dirname=(str(source), str(dest)),
                include_paths=[str(include_path) for include_path in includes],
                source_comments=use_dev_settings,
                output_style=("nested" if use_dev_settings else "compressed"),
            )
        click.secho(f"      Compiled.", fg="green")
        # For Sass files without explicit RTL versions, generate
        # an RTL version of the CSS using the rtlcss library.
        for sass_path in glob.glob(str(source) + "/**/*.scss"):
            if Path(sass_path).name.startswith("_"):
                # Don't generate RTL CSS for partials
                continue
            if sass_path.endswith("-rtl.scss"):
                # Don't generate RTL CSS if the file is itself an RTL version
                continue
            if Path(sass_path.replace(".scss", "-rtl.scss")).exists():
                # Don't generate RTL CSS if there is an explicit Sass version for RTL
                continue
            click.echo("      Generating missing right-to-left CSS:")
            source_css_file = sass_path.replace(str(source), str(dest)).replace(
                ".scss", ".css"
            )
            target_css_file = source_css_file.replace(".css", "-rtl.css")
            click.echo(f"         Source: {source_css_file}")
            click.echo(f"         Target: {target_css_file}")
            if not dry:
                subprocess.run(["rtlcss", source_css_file, target_css_file])
            click.secho("         Generated.", fg="green")

    # Information
    click.secho(f"USING ENV: {NORMALIZED_ENVS[env]}", fg="blue")
    if dry:
        click.secho(f"DRY RUN: Will print compile steps, but will not compile anything.", fg="blue")
    click.echo()

    # Warnings
    click.secho("WARNING: `npm run compile-sass` is experimental. Use at your own risk.", fg="yellow", bold=True)
    if show_help:
        click.echo(context.get_help())
        return
    if skip_lms and skip_cms:
        click.secho("WARNING: You are skipping both LMS and CMS... nothing will be compiled!", fg="yellow")
    if skip_default and skip_themes:
        click.secho("WARNING: You are skipped both default Sass and themed Sass... nothing will be compiled!", fg="yellow")
    click.echo()

    # Build a list of theme paths:
    if skip_themes:
        theme_paths = []
    else:
        theme_paths = [
            theme_dir / theme
            # For every theme dir,
            for theme_dir in theme_dirs
            for theme in (
                # for every theme name (if theme names provided),
                themes
                or
                # or for every subdir of theme dirs (if no theme name provided),
                (theme_dir_entry.name for theme_dir_entry in theme_dir.iterdir())
            )
            # consider the path a theme if it has a lms/ or cms/ subdirectory.
            if (theme_dir / theme / "lms").is_dir() or (theme_dir / theme / "cms").is_dir()
        ]

    # We expect this script to be run from the edx-platform root.
    repo = Path(".")
    if not (repo / "xmodule").is_dir():
        # Sanity check: If the xmodule/ folder is missing, we're definitely not at the root
        # of edx-platform, so save the user some headache by exiting early.
        raise Exception(f"{__file__} must be run from the root of edx-platform")

    # Every Sass compilation will use have these directories as lookup paths,
    # regardless of theme.
    common_includes = [
        repo / "common" / "static",
        repo / "common" / "static" / "sass",
        repo / "node_modules" / "@edx",
        repo / "node_modules",
    ]

    if not skip_default:
        click.secho(f"Compiling default Sass...", fg="cyan", bold=True)
        if not skip_lms:
            compile_sass_dir(
                "Compiling default LMS Sass",
                repo / "lms" / "static" / "sass",
                repo / "lms" / "static" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                ],
            )
            compile_sass_dir(
                "Compiling default certificate Sass",
                repo / "lms" / "static" / "certificates" / "sass",
                repo / "lms" / "static" / "certificates" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                ],
            )
            compile_sass_dir(
                "Compiling built-in XBlock Sass for default LMS",
                repo / "xmodule" / "assets",
                repo / "lms" / "static" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                    repo / "cms" / "static" / "sass",
                ],
            )
        if not skip_cms:
            compile_sass_dir(
                "Compiling default CMS Sass",
                repo / "cms" / "static" / "sass",
                repo / "cms" / "static" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass",
                ],
            )
            compile_sass_dir(
                "Compiling built-in XBlock Sass for default CMS",
                repo / "xmodule" / "assets",
                repo / "cms" / "static" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                    repo / "cms" / "static" / "sass",
                ],
            )
        click.secho(f"Done compiling default Sass!", fg="cyan", bold=True)
        click.echo()

    for theme in theme_paths:
        click.secho(f"Compiling Sass for theme at {theme}...", fg="cyan", bold=True)
        if not skip_lms:
            compile_sass_dir(
                "Compiling default LMS Sass with themed partials",
                repo / "lms" / "static" / "sass",
                theme / "lms" / "static" / "css",
                includes=[
                    *common_includes,
                    theme / "lms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                ],
                tolerate_missing=True,
            )
            compile_sass_dir(
                "Compiling themed LMS Sass as overrides to CSS from previous step",
                theme / "lms" / "static" / "sass",
                theme / "lms" / "static" / "css",
                includes=[
                    *common_includes,
                    theme / "lms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                ],
                tolerate_missing=True,
            )
            compile_sass_dir(
                "Compiling themed certificate Sass",
                theme / "lms" / "static" / "certificates" / "sass",
                theme / "lms" / "static" / "certificates" / "css",
                includes=[
                    *common_includes,
                    theme / "lms" / "static" / "sass" / "partials",
                    theme / "lms" / "static" / "sass",
                ],
                tolerate_missing=True,
            )
            compile_sass_dir(
                "Compiling built-in XBlock Sass for themed LMS",
                repo / "xmodule" / "assets",
                theme / "lms" / "static" / "css",
                includes=[
                    *common_includes,
                    theme / "lms" / "static" / "sass" / "partials",
                    theme / "cms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                    repo / "cms" / "static" / "sass",
                ],
            )
        if not skip_cms:
            compile_sass_dir(
                "Compiling default CMS Sass with themed partials",
                repo / "cms" / "static" / "sass",
                theme / "cms" / "static" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    theme / "cms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass",
                ],
                tolerate_missing=True,
            )
            compile_sass_dir(
                "Compiling themed CMS Sass as overrides to CSS from previous step",
                theme / "cms" / "static" / "sass",
                theme / "cms" / "static" / "css",
                includes=[
                    *common_includes,
                    repo / "lms" / "static" / "sass" / "partials",
                    theme / "cms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass",
                ],
                tolerate_missing=True,
            )
            compile_sass_dir(
                "Compiling built-in XBlock Sass for themed CMS",
                repo / "xmodule" / "assets",
                theme / "cms" / "static" / "css",
                includes=[
                    *common_includes,
                    theme / "lms" / "static" / "sass" / "partials",
                    theme / "cms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass" / "partials",
                    repo / "cms" / "static" / "sass" / "partials",
                    repo / "lms" / "static" / "sass",
                    repo / "cms" / "static" / "sass",
                ],
            )
        click.secho(f"Done compiling Sass for theme at {theme}!", fg="cyan", bold=True)
        click.echo()

    # Report what we did.
    click.secho("Successfully compiled:", fg="green", bold=True)
    if not skip_default:
        click.secho(f"  - {repo.absolute()} (default Sass)", fg="green")
    for theme in theme_paths:
        click.secho(f"  - {theme}", fg="green")
    if skip_lms:
        click.secho(f"(skipped LMS)", fg="yellow")
    if skip_cms:
        click.secho(f"(skipped CMS)", fg="yellow")


if __name__ == "__main__":
    main(prog_name="npm run compile-sass --")

#!/usr/bin/env python
"""
TODO
"""
from __future__ import annotations

import glob
import subprocess
from pathlib import Path

import click
import sass


DIR_ARG = click.Path(
    exists=True, file_okay=False, readable=True, writable=True, path_type=Path
)


@click.option(
    "-t",
    "--theme",
    "theme_paths",
    metavar="PATH",
    multiple=True,
    type=DIR_ARG,
)
@click.option(
    "-T",
    "--themes",
    "theme_parents",
    metavar="PATH",
    multiple=True,
    type=DIR_ARG,
)
@click.option(
    "--skip-default",
    is_flag=True,
)
@click.option(
    "--skip-lms",
    is_flag=True,
)
@click.option(
    "--skip-cms",
    is_flag=True,
)
@click.option(
    "--env",
    envvar="NODE_ENV",
    type=click.Choice(
        ("development", "production"),
        token_normalzation_func=(
            # Accept 'dev' and 'prod' since that's what our old tooling used,
            # but expand the value to the full word because that's what NODE_ENV uses.
            lambda value: {"dev": "development", "prod", "production"}.get(value),
        ),
    ),
)
@click.option(
    "--dry",
    is_flag=True,
)
@click.option(
    "-h",
    "--help",
    "show_help",
    is_flag=True,
    help="Print this help",
)
@click.command()
@click.pass_context
def main(
    context: click.Context,
    theme_paths: list[Path],
    theme_parents: list[Path],
    skip_default: bool,
    skip_lms: bool,
    skip_cms: bool,
    env: str,
    dry: bool,
    show_help: bool,
) -> None:
    """
    TODO
    """

    def compile_sass_dir(
        message: str,
        source: Path,
        dest: Path,
        includes: list[Path],
        tolerate_missing: bool = False,
    ) -> None:
        """
        TODO
        """
        use_dev_settings = (env == "development")
        click.echo(f"  {message}...")
        click.echo(f"      Source:      {source}")
        click.echo(f"      Destination: {dest}")
        if not source.is_dir():
            if tolerate_missing:
                click.echo(f"    Skipped because source directory does not exist.")
                return
            else:
                raise FileNotFoundError(f"missing Sass source dir: {source}")
        click.echo(f"      Include paths:")
        for include in includes:
            click.echo(f"        {include}")
        if not dry:
            dest.mkdir(parents=True, exist_ok=True)
            sass.compile(
                dirname=(str(source), str(dest)),
                include_paths=[str(include_path) for include_path in includes],
                source_comments=use_dev_settings,
                output_style=("nested" if use_dev_settings else "compressed"),
            )
        click.echo(f"    Compiled.")
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
            click.echo("    Generating missing right-to-left Sass:")
            source_css_file = sass_path.replace(str(source), str(dest)).replace(
                ".scss", ".css"
            )
            target_css_file = source_css_file.replace(".css", "-rtl.css")
            click.echo(f"         {source_css_file} -> ")
            click.echo(f"         {target_css_file}")
            if not dry:
                subprocess.run(["rtlcss", source_css_file, target_css_file])

    if show_help:
        click.echo(context.get_help())
        return

    if skip_cms and skip_lms:
        click.echo("Skipping both CMS and LMS... nothing to do! Will exit.")
        return

    repo = Path(".")
    all_theme_paths = [
        *theme_paths,
        *[
            theme_path
            for theme_parent in theme_parents
            for theme_path in theme_parent.iterdir()
            if (theme_path / "lms").exists() or (theme_path / "cms").exists()
        ],
    ]
    common_includes = [
        repo / "common" / "static",
        repo / "common" / "static" / "sass",
        repo / "node_modules" / "@edx",
        repo / "node_modules",
    ]

    if not skip_default:
        click.echo(f"Compiling default Sass...")
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
        click.echo(f"Done compiling default Sass!")

    for theme in all_theme_paths:
        click.echo(f"Compiling Sass for theme at {theme}...")

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
        click.echo(f"Done compiling Sass for theme at {theme}!")

    click.echo()
    click.echo("Successfully compiled:")
    if not skip_default:
        click.echo(f"  - {repo.absolute()} (default Sass)")
    for theme in all_theme_paths:
        click.echo(f"  - {theme}")
    if skip_cms:
        click.echo(f"(skipped CMS)")
    if skip_lms:
        click.echo(f"(skipped LMS)")


def should_generate_rtl_css_file(sass_file: Path):
    """
    Returns true if a Sass file should have an RTL version generated.
    """
    return not (
        # Don't generate RTL CSS for partials
        sass_file.name.startswith("_")
        # Don't generate RTL CSS if the file is itself an RTL version
        or sass_file.name.endswith("-rtl.scss")
        # Don't generate RTL CSS if there is an explicit Sass version for RTL
        or Path(str(sass_file).replace(".scss", "-rtl.scss")).exists()
    )


if __name__ == "__main__":
    main()

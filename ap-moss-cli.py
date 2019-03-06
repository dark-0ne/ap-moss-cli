#!/usr/bin/python3
import os
import argparse
import shutil
import requests
import re

import github


def __version__():
    return "1.0.0"


def cleanup_dirs(wd, project_name):
    """Removes specified project repos directory."""
    shutil.rmtree(os.path.join(wd, 'repos', project_name), ignore_errors=True)


def setup_dirs(wd, project_name):
    """Creates required directories for specified project."""

    # pylint: disable=E1123
    os.makedirs(
        os.path.join(wd, 'repos', project_name, "starter"), exist_ok=True)


def connect_github(token=None, username=None, pwd=None):
    """Connects to github either with a token or username/pwd."""
    if token is None:
        return github.Github(username, pwd)
    else:
        return github.Github(token)


def download_starter(wd, project_name, g):
    """Downloads src java files from specified project starter repo."""

    try:
        repo = g.get_repo("k-n-toosi-university-of-technology/" +
                          project_name + '-starter')
        src_files = repo.get_contents("src/main/java/ir/ac/kntu")
        for src in src_files:
            r = requests.get(src.download_url)
            with open(
                    os.path.join(wd, "repos", project_name, "starter",
                                 src.name), 'wb') as f:
                f.write(r.content)
    except github.GithubException as e:
        if e.status == 401:
            print(
                "\nInvalid credentials. Check your github token/username-pwd.")
        elif e.status == 404:
            print(
                "\nCould not find starter repo. Maybe incorrect project name?")
        else:
            print("\nProblem downloading starter repo. More info:")
            print(e)

        terminate(wd, project_name)


def download_students(wd, project_name, g, due):
    """Downloads src java files from specified project students repo."""

    org = g.get_organization("k-n-toosi-university-of-technology")
    collaborators = org.get_outside_collaborators()
    map(lambda x: x.login, collaborators)

    for student in collaborators:
        repo = g.get_repo("k-n-toosi-university-of-technology")


def setup_moss_script(moss_id):
    """Creates new moss perl script with provided moss user_id."""
    with open("moss-starter.pl", "r") as read_file:
        with open("mossnet.pl", "w") as write_file:
            for line in read_file.readlines():
                if line.startswith("$userid"):
                    line = re.sub(r"[0-9]+", str(moss_id), line)
                write_file.write(line)
    os.chmod("mossnet.pl", 0o777)


def moss_compare(wd, project_name):
    """Calls created perl script with required parameters."""

    repos_dir = os.path.join(wd, 'repos', project_name)

    command = './mossnet.pl -l python -m 4'

    for starter_src in os.listdir(os.path.join(repos_dir, 'starter')):
        command += ' -b '
        command += os.path.join(repos_dir, "starter", starter_src)

    command += ' -d '
    command += os.path.join(repos_dir, "students", "**", "*.java")

    os.system(command)


def terminate(wd, project_name):
    print("Cleaning up created directories before terminating!")
    cleanup_dirs(wd, project_name)
    raise SystemExit


class CustomHelpFormatter(argparse.HelpFormatter):
    """
    Formats argparse help output
    """

    # pylint: disable=E1004, E1101

    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=100)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)
        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ', '.join(action.option_strings) + ' ' + args_string


def main():

    # Setup arg parser
    fmt = lambda prog: CustomHelpFormatter(prog)  # noqa
    parser = argparse.ArgumentParser(
        description=  # noqa
        'Checks for code similarity in AP github repositories using MossNet.',
        prog="ap-moss-cli",
        formatter_class=fmt,
        epilog="In case you dont have a moss user id visit" +
        " http://theory.stanford.edu/~aiken/moss/")
    parser.add_argument(
        "project",
        metavar="project_name",
        help="Name of the project on the organization")
    parser.add_argument(
        "-u",
        "--username",
        nargs='?',
        help="Github username. If not provided will instead look for token in"
        + " env variable AP_MOSS_TOKEN")
    parser.add_argument("-p", "--password", nargs='?', help="Github password")
    parser.add_argument(
        "-o",
        "--output",
        nargs='?',
        default=os.getcwd(),
        help="Path for storing downloaded repos. defaults to cwd/repos")
    parser.add_argument(
        "-f",
        "--force_cleanup",
        nargs='?',
        default=False,
        metavar='',
        const=True,
        help="Delete downloaded repo files after script is done.")
    parser.add_argument(
        "--mid",
        metavar="MOSS ID",
        dest="moss_id",
        nargs='?',
        help="Moss id used for sending requests. If not provided will look for"
        + " env variable MOSS_ID.")
    parser.add_argument(
        "-v",
        "--version",
        action='version',
        version="%(prog)s " + __version__())

    args = parser.parse_args()

    # Check for username and pwd
    if args.username is None:
        try:
            args.token = os.environ["AP_MOSS_TOKEN"]
        except KeyError:
            print(
                "Please provide either username/pwd or auth token for github.")
            terminate(args.output, args.project)
    else:
        args.token = None

    if args.moss_id is None:
        try:
            args.moss_id = os.environ["MOSS_ID"]
        except KeyError:
            print("Please provide Moss id either through paramaters or" +
                  "env variables.")
            terminate(args.output, args.project)

    # Setup

    print("Setting up directories")
    setup_dirs(args.output, args.project)

    g = connect_github(args.token, args.username, args.password)

    print("Downloading starter repository")
    download_starter(args.output, args.project, g)

    # print("Downloading student repositories")
    # download_students(args.ouput, args.project, g)

    print("Setting up moss script")
    setup_moss_script(args.moss_id)

    print("Comparing files")
    moss_compare(args.output, args.project)

    # Cleanup
    if args.force_cleanup:
        print("Cleaning up directories")
        cleanup_dirs(args.output, args.output)


if __name__ == '__main__':
    main()

#!/usr/bin/python3
import os
import argparse
import shutil
import requests
import re
import datetime
import webbrowser
import base64

import gitlab
from tqdm import tqdm
import mosspy


def __version__():
    return "1.1.0"


def cleanup_dirs(wd, project_name):
    """Removes specified project repos directory."""
    shutil.rmtree(os.path.join(wd, 'repos', project_name), ignore_errors=True)
    shutil.rmtree(os.path.join(wd, 'outs', project_name), ignore_errors=True)


def setup_dirs(wd, project_name):
    """Creates required directories for specified project."""

    # pylint: disable=E1123
    os.makedirs(
        os.path.join(wd, 'repos', project_name, "starter"), exist_ok=True)

    os.makedirs(os.path.join(wd, 'outs', project_name), exist_ok=True)


def connect_gitlab(url, token=None, email=None, pwd=None):
    
    """Connects to github either with a token or username/pwd."""

    if token is None:
        return gitlab.Gitlab(url, email=email, password=pwd)
    else:
        print(url, token)
        return gitlab.Gitlab(url, private_token=token)



def download_starter(wd, project_name, g):
    """Downloads src java files from specified project starter repo."""

    try:
        print(project_name) 
        repo = g.projects.list(search=project_name).pop()
        print(repo)

        # TODO: support user provided paths
        src_files = repo.repository_tree("src/main/java/ir/ac/kntu", recursive=True)
        for src in tqdm(src_files, "Downloading starter repository"):
            if re.match(r"\w*\.java$", src['name']):
                print(src, '\n')
                file_info = repo.repository_blob(src['id'])
                content = base64.b64decode(file_info['content'])
                with open(
                        os.path.join(wd, "repos", project_name, "starter",
                                     src['name']), 'wb') as f:
                    f.write(content)

    except gitlab.exceptions.GitlabError as e:
        print(e)

        terminate(wd, project_name)


def download_students(wd, project_name, g, due):
    """Downloads src java files from specified project students repo."""

    empty_or_no_repo = 0
    no_valid_commit = 0
    java_pattern = re.compile(r'\w*\.java$')

    print(project_name) 
    repos = g.projects.list(search=project_name)
    print(repos)

    # TODO: support user provided paths

    try:
        for repo in repos: 
            src_files = repo.repository_tree("src/main/java/ir/ac/kntu", recursive=True)
            for src in tqdm(src_files, "Downloading starter repository"):
                if re.match(r"\w*\.java$", src['name']):
                    print(src, '\n')
                    file_info = repo.repository_blob(src['id'])
                    content = base64.b64decode(file_info['content'])
                    name = repo.owner['name']
            # TODO: support user provided paths
                    student_path = os.path.join(wd, 'repos', project_name, "students",
                                        name)
                    # pylint: disable=E1123
                    os.makedirs(student_path, exist_ok=True)
                    with open(os.path.join(student_path, src['name']),
                            'wb') as f:
                        f.write(content)

    except gitlab.GitlabError as e:
        if e.status == 404 or e.status == 409:
            empty_or_no_repo += 1
        else:
            print("Could not get " + str(name) + ". More info:")
            print(e)
            terminate(wd, project_name)

    except IndexError:
        no_valid_commit += 1

    except requests.exceptions.MissingSchema:
        pass

    return empty_or_no_repo, no_valid_commit


def run_mosspy(wd, project_name, m, uid):

    mpy = mosspy.Moss(uid, "python")
    mpy.setIgnoreLimit(m)
    repos_dir = os.path.join(wd, 'repos', project_name)

    for starter_src in os.listdir(os.path.join(repos_dir, 'starter')):
        mpy.addBaseFile(os.path.join(repos_dir, 'starter', starter_src))

    mpy.addFilesByWildcard(os.path.join(repos_dir, "students", "*", "*.java"))
    report_url = mpy.send()
    print("Report url: " + report_url)

    return report_url


def download_report(wd, project_name, report_url):

    outs_dir = os.path.join(wd, "outs", project_name)

    mosspy.download_report(
        report_url, os.path.join(outs_dir, "report.html"), connections=8)


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
        "--due",
        metavar="YYYY-MM-DD-HH",
        help="Homework deadline time. Defaults to datetime.now()")
    parser.add_argument(
        "-o",
        "--output",
        nargs='?',
        default=os.getcwd(),
        help="Path for storing downloaded repos. defaults to cwd/repos")
    parser.add_argument(
        "-s",
        "--skip-github",
        action="store_true",
        help=  # noqa
        "Skip downloading student and starter repos from github and use local"
        + " files instead")
    parser.add_argument(
        "-f",
        "--force-cleanup",
        action="store_true",
        help="Delete downloaded repo files after script is done")
    parser.add_argument(
        "--skip-report",
        action="store_true",
        help="Skip downloading report and just print report url")
    parser.add_argument(
        "--mid",
        metavar="MOSS ID",
        dest="moss_id",
        nargs='?',
        help="Moss id used for sending requests. If not provided will look for"
        + " env variable MOSS_ID")
    parser.add_argument(
        "-m", nargs='?', default=4, help="m parameter used in moss script")
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

    # Check for moss_id
    if args.moss_id is None:
        try:
            args.moss_id = os.environ["MOSS_ID"]
        except KeyError:
            print("Please provide Moss id either through paramaters or" +
                  "env variables.")
            terminate(args.output, args.project)

    # Parse deadline time
    if args.due is None:
        args.due = datetime.datetime.now()
    else:
        args.due = datetime.datetime.strptime(args.due, "%Y-%m-%d-%H")

    g = connect_gitlab('http://apj.ce.kntu.ac.ir/git', args.token)

    if not args.skip_github:
        # Setup
        print("Setting up directories")
        cleanup_dirs(args.output, args.project)
        setup_dirs(args.output, args.project)

        download_starter(args.output, args.project, g)

        empty_repos, invalid_commits = download_students(
            args.output, args.project, g, args.due)

        print("{} with empty/no repos; {} with no commits before deadline".
              format(empty_repos, invalid_commits))

    print("Running mosspy")
    report_url = run_mosspy(args.output, args.project, args.m, args.moss_id)

    if args.skip_report:
        webbrowser.open_new_tab(report_url)
    else:
        print("Saving report")
        download_report(args.output, args.project, report_url)

    # Cleanup
    if args.force_cleanup:
        print("Cleaning up repo directories")
        shutil.rmtree(
            os.path.join(args.output, 'repos', args.project),
            ignore_errors=True)


if __name__ == '__main__':
    main()

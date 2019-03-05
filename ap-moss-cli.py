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
    shutil.rmtree(os.path.join(wd, 'repos', project_name), ignore_errors=True)


def startup_dirs(wd, project_name):
    os.makedirs(
        os.path.join(wd, 'repos', project_name, "starter"), exist_ok=True)


def connect_github(token=None, username=None, pwd=None):
    if token is None:
        return github.Github(username, pwd)
    else:
        return github.Github(token)


def download_starter(wd, project_name, g):

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
        print(e)
        print(
            "\nProblem downloading starter repo. Maybe incorrect project name?"
        )
        print("Terminating!")
        raise SystemExit


def setup_moss_script(moss_id):
    with open("moss-starter.pl", "r") as read_file:
        with open("mossnet.pl", "w") as write_file:
            for line in read_file.readlines():
                if line.startswith("$userid"):
                    line = re.sub(r"[0-9]+", str(moss_id), line)
                write_file.write(line)
    os.chmod("mossnet.pl", 0o777)


def moss_compare(wd, project_name):

    repos_dir = os.path.join(wd, 'repos', project_name)

    command = './mossnet.pl -l python -m 4'

    for starter_src in os.listdir(os.path.join(repos_dir, 'starter')):
        command += ' -b '
        command += os.path.join(repos_dir, "starter", starter_src)

    command += ' -d '
    command += os.path.join(repos_dir, "students", "**", "*.java")

    os.system(command)


def main():

    # Setup arg parser
    parser = argparse.ArgumentParser(
        description=
        'Checks for code similarity in AP github repositories using MossNet.',
        prog="ap-moss-cli",
        epilog="In case you dont have a moss user id visit" +
        " http://theory.stanford.edu/~aiken/moss/")
    parser.add_argument(
        "project", help="Name of the project on the organization")
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
        const=True,
        help="deletes previous output files and repos")
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
                "Please provide either username/pwd or auth token for github."
                + " \nTerminating!")
            raise SystemExit

    if args.moss_id is None:
        try:
            args.moss_id = os.environ["MOSS_ID"]
        except KeyError:
            print("Please provide Moss id either through paramaters or" +
                  "env variables.\nTerminating!")
            raise SystemExit

    # Cleanup and setup
    if args.force_cleanup:
        print("Cleaning up directories")
        cleanup_dirs(args.output, args.output)

    print("Setting up directories")
    startup_dirs(args.output, args.project)

    print("Downloading starter repository")
    download_starter(args.output, args.project,
                     connect_github(args.token, args.username, args.password))

    print("Comparing files")
    moss_compare(args.output, args.project)


if __name__ == '__main__':
    main()

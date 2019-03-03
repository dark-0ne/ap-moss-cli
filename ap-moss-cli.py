#!/usr/bin/python3
import os
import argparse
import shutil
import requests

from github import Github


def cleanup_dirs(wd, project_name):
    shutil.rmtree(os.path.join(wd, 'repos', project_name), ignore_errors=True)
    shutil.rmtree(os.path.join(wd, 'out', project_name), ignore_errors=True)


def startup_dirs(wd, project_name):
    os.makedirs(os.path.join(wd, 'repos', project_name), exist_ok=True)
    os.makedirs(os.path.join(wd, 'out', project_name), exist_ok=True)


def connect_github(token=None, username=None, pwd=None):
    if token is None:
        return Github(username, pwd)
    else:
        return Github(token)


def download_starter(wd, project_name, g):

    repo = g.get_repo("k-n-toosi-university-of-technology/" + project_name +
                      '-starter')
    src_files = repo.get_contents("src/main/java/ir/ac/kntu")

    for src in src_files:
        r = requests.get(src.download_url)
        with open(os.path.join(wd, "repos", project_name, src.name),
                  'wb') as f:
            f.write(r.content)


def main():

    # Setup arg parser
    parser = argparse.ArgumentParser(
        description=
        'Checks for code similarity in AP github repositories using MossNet.',
        prog="ap-moss-cli")
    parser.add_argument(
        "project", help="Name of the project on the organization")
    parser.add_argument(
        "-u",
        "--username",
        nargs='?',
        help="Github username. If not provided will look for token in env" +
        " variable AP_MOSS_TOKEN")
    parser.add_argument("-p", "--password", nargs='?', help="Github password")
    parser.add_argument(
        "-o",
        "--output",
        nargs='?',
        default=os.getcwd(),
        help="Output files path. defaults to current working directory")
    parser.add_argument(
        "-f",
        "--force_cleanup",
        nargs='?',
        default=False,
        const=True,
        help="Deletes previous output files and repos")

    args = parser.parse_args()

    # Check for username and pwd
    if args.username is None:
        try:
            args.token = os.environ["AP_MOSS_TOKEN"]
        except KeyError:
            print(
                "Please provide either username/pwd or auth token for github."
                + " Terminating!")
            raise SystemExit

    # Cleanup and setup
    if args.force_cleanup:
        cleanup_dirs(args.output, args.output)

    startup_dirs(args.output, args.project)

    download_starter(args.output, args.project,
                     connect_github(args.token, args.username, args.password))


if __name__ == '__main__':
    main()

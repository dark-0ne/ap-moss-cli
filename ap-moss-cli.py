#!/usr/bin/python3
import os
import argparse
import shutil
import requests
import mosspy

from github import Github


def cleanup_dirs(wd, project_name):
    shutil.rmtree(os.path.join(wd, 'repos', project_name), ignore_errors=True)
    shutil.rmtree(os.path.join(wd, 'out', project_name), ignore_errors=True)


def startup_dirs(wd, project_name):
    os.makedirs(
        os.path.join(wd, 'repos', project_name, "starter"), exist_ok=True)
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
        with open(
                os.path.join(wd, "repos", project_name, "starter", src.name),
                'wb') as f:
            f.write(r.content)


def moss_compare(wd, project_name, moss_id):

    repos_dir = os.path.join(wd, 'repos', project_name)
    out_dir = os.path.join(wd, 'out', project_name)

    m = mosspy.Moss(717626159, "python")
    m.setDirectoryMode(True)
    m.setIgnoreLimit(4)

    for starter_src in os.listdir(os.path.join(repos_dir, 'starter')):
        m.addBaseFile(os.path.join(repos_dir, "starter", starter_src))

    m.addFilesByWildcard(
        os.path.join(repos_dir, "students", "*",
                     "src/main/java/ir/ac/kntu/*.java"))

    report_url = m.send()
    print("Report Url: " + report_url)
    m.saveWebPage(report_url, "submission/report.html")

    mosspy.download_report(report_url, out_dir, connections=8)


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
        help="deletes previous output files and repos")
    parser.add_argument(
        "--mid",
        metavar="MOSS ID",
        dest="moss_id",
        nargs='?',
        help="Moss id used for sending requests. If not provided will look for"
        + " env variable MOSS_ID. In case you dont have one visit" +
        " http://theory.stanford.edu/~aiken/moss/")

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

    if args.moss_id is None:
        try:
            args.moss_id = os.environ["MOSS_ID"]
        except KeyError:
            print("Please provide Moss id either through paramaters or" +
                  "env variables. Terminating!")
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
    moss_compare(args.output, args.project, args.moss_id)


if __name__ == '__main__':
    main()

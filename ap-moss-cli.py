#!/usr/bin/python3
import os
import argparse
import shutil


def cleanup(wd):
    shutil.rmtree(os.path.join(wd, 'repos'), ignore_errors=True)
    shutil.rmtree(os.path.join(wd, 'out'), ignore_errors=True)


def startup(wd):
    os.makedirs(os.path.join(wd, 'repos'), exist_ok=True)
    os.makedirs(os.path.join(wd, 'out'), exist_ok=True)


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
        help="Github username. Can also be set via env variable AP_MOSS_USER")
    parser.add_argument(
        "-p",
        "--password",
        nargs='?',
        help="Github password. Can also be set via env variable AP_MOSS_PWD")
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
        help="Clean up previous output files and repos")

    args = parser.parse_args()

    # Check for username and pwd
    if args.username is None:
        try:
            args.username = os.environ['AP_MOSS_USER']
        except KeyError:
            print(
                "Provide username either through parameteres or env variables."
                + " Terminating!")
            raise SystemExit

    if args.password is None:
        try:
            args.password = os.environ['AP_MOSS_PWD']
        except KeyError:
            print(
                "Provide password either through parameteres or env variables."
                + " Terminateing!")
            raise SystemExit

    # Cleanup and setup
    if args.force_cleanup:
        cleanup(args.output)

    startup(args.output)


if __name__ == '__main__':
    main()

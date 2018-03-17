#!/usr/bin/env python3
from argparse import ArgumentParser
from datetime import datetime
import json
import os, os.path
import re
from subprocess import run, PIPE, Popen
import sys
import time

import dateparser
import psycopg2


PORT = os.getenv("SHELLMINE_PORT") or 15432
IMAGE = os.getenv("SHELLMINE_IMAGE") or "shell-mining"
NAME_CONTAINER = os.getenv("SHELLMINE_CONTAINER") or "shell-mining"
VOLUME_DB = os.getenv("SHELLMINE_DB") or os.path.expandvars("$HOME/.shell-mining")


class Timeout(Exception):
    pass

class NoImage(Exception):
    pass

class IllFormattedStdin(Exception):
    pass


def is_db_running(dev_null):
    r = run(["docker", "inspect", NAME_CONTAINER], shell=False, stdout=PIPE, stderr=dev_null, encoding="utf8")
    if r.returncode == 0:
        resp = json.loads(r.stdout)
        return isinstance(resp, list) and \
            len(resp) > 0 and \
            isinstance(resp[0], dict) and \
            resp[0].get("State", {}).get("Status", "None") == "running"
    else:
        return False


def check_image_present(dev_null):
    if len(
        run(
            ["docker", "images", "--quiet", IMAGE],
            shell=False,
            check=True,
            stdout=PIPE,
            stderr=dev_null,
            encoding="utf8"
        ).stdout.strip()
    ) == 0:
        raise NoImage()


def ensure_db_runs():
    with open("/dev/null", "w") as dev_null:
        if not is_db_running(dev_null):
            check_image_present(dev_null)
            os.makedirs(VOLUME_DB, exist_ok=True)
            run(
                ["docker", "run", "--rm", "--detach",
                    "--name", NAME_CONTAINER,
                    "--publish", "{}:5432".format(PORT),
                    "--volume", os.path.abspath(VOLUME_DB) + ":/var/lib/postgresql/data",
                    IMAGE],
                check=True,
                shell=False,
                stdout=dev_null,
                stderr=dev_null
                )


def connect_db():
    timeout = time.time() + float(os.getenv("SHELLMINE_DB_TIMEOUT") or "60.0")
    while True:
        if time.time() > timeout:
            raise Timeout()
        ensure_db_runs()
        try:
            return psycopg2.connect(
                host = os.getenv("SHELLMINE_HOST") or "127.0.0.1",
                port = int(os.getenv("SHELLMINE_PORT") or "15432"),
                user = os.getenv("SHELLMINE_USER") or "shellmine",
                password = os.getenv("SHELLMINE_PASSWORD") or "shellmine",
                database = "shellmining"
            )
        except psycopg2.OperationalError as err:
            time.sleep(0.1)


def read_cmd_line():
    # This program expects that the standard output of the history bash command is expected
    # as standard input to this command, with HISTTIMEFORMAT set so as to produce two blank-
    # separated tokens, respectively for the current date and time. Typical usage:
    #
    # PROMPT_COMMAND='X=$? && HISTTIMEFORMAT="%Y-%m-%d %H:%M:%S" history 1 | shellmine -x $X'
    line_stripped = sys.stdin.readline().strip()
    if len(line_stripped) > 0:
        _, ts_date, ts_time, cmd = line_stripped.split(maxsplit=3)
        return dateparser.parse("{} {}".format(ts_date, ts_time)), cmd.strip()
    else:
        raise IllFormattedStdin()


if __name__ == '__main__':

    argument_parser = ArgumentParser(
        description="Tool for acquiring command lines and analyzing their frequency."
    )
    argument_parser.add_argument(
        "-x EXIT-CODE",
        "--exit-code EXIT-CODE",
        help="Pushes the latest command line into the database, then exits with given exit code. "
             "If this parameter is provided, then all others are ignored.",
        dest="exit_code",
        type=int,
        default=None
    )
    argument_parser.add_argument(
        "--from TS-FROM",
        help="Lower time bound for the command line query.",
        type=dateparser.parse,
        dest="ts_from",
        default=datetime.min
    )
    argument_parser.add_argument(
        "--to TS-TO",
        help="Upper time bound for the command line query.",
        type=dateparser.parse,
        dest="ts_to",
        default=datetime.max
    )
    argument_parser.add_argument(
        "-n NUM-RESULTS",
        help="Prints at most this number of results from frequency aggregation.",
        type=int,
        dest="num_results",
        default=10
    )
    argument_parser.add_argument(
        "prefix",
        nargs="*",
        help="Words that should prefix the commands to aggregate.",
        default=""
    )
    ns = argument_parser.parse_args()

    exit_code = 0
    try:
        with connect_db() as dbx, dbx.cursor() as cur:

            if ns.exit_code is not None:

                timestamp, cmd_line = read_cmd_line()
                cur.execute(
                    "insert into cmdline(ts, cmd) values (%s, %s)",
                    (timestamp, cmd_line)
                    )

            else:

                cur.execute(
                    "select count(cmd) as cnt, max(ts) as last, cmd from cmdline "
                        "where position(%s in cmd) = 1 and "
                              "ts >= %s and "
                              "ts <= %s "
                        "group by cmd "
                        "order by cnt desc, last desc "
                        "limit %s",
                    (" ".join(ns.prefix), ns.ts_from, ns.ts_to, ns.num_results)
                )
                print(
                    json.dumps(
                        [
                            {
                                "count": count,
                                "cmd": cmd,
                                "ts_last": {
                                    "from_epoch": ts_last.timestamp(),
                                    "iso":        ts_last.isoformat()
                                }
                            }
                            for count, ts_last, cmd in cur
                        ],
                        indent=2
                    )
                )

    except Timeout:
        print("Timed out while connecting to database.", file=sys.stderr)
        exit_code = 1

    except NoImage:
        print(
            f"Docker image {SHELLMINE_IMAGE} could not be found. Have you built and installed the tool properly?",
            file=sys.stderr
            )
        exit_code = 2

    except IllFormattedStdin:
        print("Ill-formatted history line; ignore.", file=sys.stderr)
        exit_code = 3

    sys.exit(ns.exit_code or exit_code)

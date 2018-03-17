# Shell mining tools

Following [this
post](http://matt.might.net/articles/console-hacks-exploiting-frequency/)
from Matt Might, I built this toolkit for capturing the commands I type on the
shell (beyond merely `.bash_history`, which fails to see many commands when
using multiple shells simultaneously), and identify which I use most frequently.
Command lines are stored in a [PostgreSQL](https://www.postgresql.org/)
database, from which they can be queried for frequency over certain time
periods, as well as in context of a certain prefix (for identifying, for
instance, the most frequent `git` sub-commands).

The capture of the shell commands is performed through setting the
`PROMPT_COMMAND` environment variable, run as a command by Bash before
expanding and displaying a prompt. This is a bit of an abuse of this Bash
feature, but the feature abuse police have yet to deliver an indictment, so I
guess they have bigger fish to catch.

## Requirements

1. Working [Docker](https://www.docker.com/) environment.
1. Bash shell (or shell backward-compatible with Bash features).
1. `make`
1. Python 3, with the following packages installed:
  1. `dateparser`
  1. `psycopg2`

## Setup

1. `make build` -- This builds the Docker image from which the PostgreSQL
   database is run.
1. `make install` -- This deploys the `shellmine` program into a directory of
   executables. By default, it is `/usr/local/bin`. Set the `PREFIX` Makefile
   variable to another directory to change that. For instance,
   ```
   make install PREFIX=$HOME/usr
   ```
   installs the `shellmine` program into `$HOME/usr/bin`.
1. `make prompt` -- Appends the definition of `PROMPT_COMMAND` to the current
   user's `.profile` file. This definition can be adjusted to enable more work
   from this feature, but such tinkering is left to the user to figure out.
 
## Configuration

The following environment variables can be set prior to setup in order to
configure the footprint of the tool:

- `SHELLMINE_IMAGE` -- Name of the Docker image built in order to run the
  database. Default: `shell-mining`
- `SHELLMINE_CONTAINER` -- Name of the container running the database. Default:
  `shell-mining`
- `SHELLMINE_DB` -- Path to the directory where the critical database files will
  be written. Default: `$HOME/.shell-mining`
- `SHELLMINE_HOST` -- Host address on which the database runs. Unless you hack
  the program and truly know what you are doing, it is suggested not to define
  this and let the default value be used: 127.0.0.1
- `SHELLMINE_PORT` -- Port to expose on the machine so the `shellmine` tool may
  connect to the database. It is forwarded to the usual PostgreSQL port 5432.
  Default: 15432
- `SHELLMINE_USER` -- PostgreSQL role used to segregate the shell mining
  database. Should be left as the default unless one hacks the code. Default:
  `shellmine`
- `SHELLMINE_PASSWORD` -- Password of the PostgreSQL role used to segregate the
  shell mining database. Should be left as the default unless one hacks the
  code. Default: `shellmine`
- `SHELLMINE_DB_TIMEOUT` -- Number of seconds during which a connection to the
  database is attempted. Default is 60.
  
**Important remark** -- The database container is created, and the database set
up, the first time a shell is started following the execution of `make prompt`.
This operation takes some 20 seconds on my machine. Therefore, if the database
connection timeout is set to something very small, it is possible that the first
commands issued following setup be dropped from the capture, with error messages
dispensed by the `shellmine` tool.

## Usage

The leveraging of the `PROMPT_COMMAND` variable effectively collects all command
lines into the database, which is put up the first time the tool is run. After
that, one can invoke `shellmine` in a standalone fashion to query the database
as to the most frequent commands.
```sh
shellmine
```
returns the 10 most commonly used commands, in reverse frequency order (and
recency of the last command instance for equal frequency), in pretty-printed
JSON format.  On my own machine, as I am writing this, the results of this
command are:
```json
[
  {
    "count": 20,
    "cmd": "shellmine",
    "ts_last": {
      "from_epoch": 1521314167.0,
      "iso": "2018-03-17T15:16:07"
    }
  },
  {
    "count": 4,
    "cmd": ". ~/.profile",
    "ts_last": {
      "from_epoch": 1521312465.0,
      "iso": "2018-03-17T14:47:45"
    }
  },
  {
    "count": 3,
    "cmd": "man bash",
    "ts_last": {
      "from_epoch": 1521316471.0,
      "iso": "2018-03-17T15:54:31"
    }
  },
  {
    "count": 3,
    "cmd": "gs",
    "ts_last": {
      "from_epoch": 1521312637.0,
      "iso": "2018-03-17T14:50:37"
    }
  },
  {
    "count": 3,
    "cmd": "gC",
    "ts_last": {
      "from_epoch": 1521312576.0,
      "iso": "2018-03-17T14:49:36"
    }
  },
  {
    "count": 3,
    "cmd": "jobs",
    "ts_last": {
      "from_epoch": 1521312166.0,
      "iso": "2018-03-17T14:42:46"
    }
  },
  {
    "count": 2,
    "cmd": "(exit 9)",
    "ts_last": {
      "from_epoch": 1521312378.0,
      "iso": "2018-03-17T14:46:18"
    }
  },
  {
    "count": 2,
    "cmd": "vim",
    "ts_last": {
      "from_epoch": 1521312236.0,
      "iso": "2018-03-17T14:43:56"
    }
  },
  {
    "count": 2,
    "cmd": "docker ps",
    "ts_last": {
      "from_epoch": 1521311994.0,
      "iso": "2018-03-17T14:39:54"
    }
  },
  {
    "count": 2,
    "cmd": "docker exec -it -u postgres shell-mining psql --username shellmine --db shellmining",
    "ts_last": {
      "from_epoch": 1521309311.0,
      "iso": "2018-03-17T13:55:11"
    }
  }
]
```
Shell purists will suggest that JSON output is harder to process using other
shell tools. You are right, dear purists, but I dare propose you to take a look
at [jq](https://stedolan.github.io/jq/) and allow me to enjoy yet my structured
data output.

To change the number of results issued, use the `-n` parameter:
```sh
shellmine -n 2
```
Result:
```json
[
  {
    "count": 20,
    "cmd": "shellmine",
    "ts_last": {
      "from_epoch": 1521314167.0,
      "iso": "2018-03-17T15:16:07"
    }
  },
  {
    "count": 4,
    "cmd": ". ~/.profile",
    "ts_last": {
      "from_epoch": 1521312465.0,
      "iso": "2018-03-17T14:47:45"
    }
  }
]
```

You can also single out a period for the analysis, using the `--from` and `--to`
parameters:
```sh
shellmine -n 5 --from '2018-03-17 15:00' --to '16:00'
```
Results:
```json
[
  {
    "count": 4,
    "cmd": "shellmine",
    "ts_last": {
      "from_epoch": 1521314167.0,
      "iso": "2018-03-17T15:16:07"
    }
  },
  {
    "count": 3,
    "cmd": "man bash",
    "ts_last": {
      "from_epoch": 1521316471.0,
      "iso": "2018-03-17T15:54:31"
    }
  },
  {
    "count": 1,
    "cmd": "shellmine | pbcopy",
    "ts_last": {
      "from_epoch": 1521316479.0,
      "iso": "2018-03-17T15:54:39"
    }
  },
  {
    "count": 1,
    "cmd": "make PREFIX=hoho",
    "ts_last": {
      "from_epoch": 1521314188.0,
      "iso": "2018-03-17T15:16:28"
    }
  },
  {
    "count": 1,
    "cmd": "make",
    "ts_last": {
      "from_epoch": 1521314180.0,
      "iso": "2018-03-17T15:16:20"
    }
  }
]
```

Finally, in order to look up the frequency of sub-commands or parameters of
certain commands, simply type the prefix:
```sh
shellmine git
```
Result:
```json
[
  {
    "count": 1,
    "cmd": "git push -u origin master",
    "ts_last": {
      "from_epoch": 1521313577.0,
      "iso": "2018-03-17T15:06:17"
    }
  },
  {
    "count": 1,
    "cmd": "git remote add origin git@github.com:hamelin/shellmine.git",
    "ts_last": {
      "from_epoch": 1521313560.0,
      "iso": "2018-03-17T15:06:00"
    }
  }
]
```

## Database management

The database runs from the Docker container `shell-mining`, unless it was named
otherwise through setting environment variable `SHELLMINE_CONTAINER`. In any
case, one may easily access the database in order to play with raw data or
remove excess data. Simply run
```sh
docker exec -it -u postgres shell-mining psql --db shell-mining
```
To connect as the `shellmine` user (or whatever else was set up through the
`SHELLMINE_USER` environment variable), append `--username shellmine` to this
command.

## Development setup

I find that, in order to facilitate the hacking of this code, it feels best to
set myself up with a directory of executables directly in my account, at
`$HONE/usr/bin`, and symlink `shellmine.py` to `$HOME/usr/bin/shellmine`. Thus,
changes to the source are deployed instantly and can be experimented with live.

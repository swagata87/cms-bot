#!/usr/bin/env python
from __future__ import print_function

import datetime
from _py2with3compatibility import HTTPError
from os.path import dirname, abspath
from socket import setdefaulttimeout
import sys

from cms_static import (
    GH_CMSSW_ORGANIZATION,
    GH_CMSSW_REPO,
)
from github_utils import (
    get_git_tag,
    create_git_tag,
    get_commits,
    find_tags,
)

from categories import CMSSW_L1

setdefaulttimeout(120)
SCRIPT_DIR = dirname(abspath(sys.argv[0]))


if __name__ == "__main__":
    from optparse import OptionParser

    parser = OptionParser(
        usage="%prog [-n|--dry-run] [-N|--release-name] [-d|--day] [-H|--hour] [-b|--branch]"
    )
    parser.add_option(
        "-n",
        "--dry-run",
        dest="dryRun",
        action="store_true",
        help="Do not modify Github",
        default=False,
    )
    parser.add_option(
        "-N",
        "--release-name",
        dest="release_name",
        action="store",
        help="CMSSW Release name",
    )
    parser.add_option(
        "-d", "--date", dest="date", action="store", help="CMSSW IB date (YYYY-MM-DD)"
    )
    parser.add_option(
        "-H", "--hour", dest="hour", action="store", help="CMSSW IB hour (HH)"
    )
    parser.add_option(
        "-b", "--branch", dest="branch", action="store", help="CMSSW branch"
    )
    parser.add_option(
        "-q", "--queue", dest="queue", action="store", help="CMSSW IB queue"
    )
    opts, args = parser.parse_args()

    RELEASE_NAME = opts.release_name  # "CMSSW_13_0_X_2023-02-02-1100"
    ib_date = datetime.datetime.strptime(
        "%s %s:00" % (opts.date, opts.hour), "%Y-%m-%d %H:%M"
    )

    RELEASE_BRANCH = opts.branch  # "master"
    QUEUE = opts.queue  # "CMSSW_13_0_X"

    repo = "%s/%s" % (GH_CMSSW_ORGANIZATION, GH_CMSSW_REPO)

    try:
        ref = get_git_tag(repo, RELEASE_NAME)
        HEAD_SHA = ref["object"]["sha"]
    except HTTPError:
        commits_ = get_commits(repo, RELEASE_BRANCH, until=ib_date, per_page=100)
        if not commits_:
            sys.exit(1)

        head = None
        for commit_ in commits_:
            if commit_["commit"]["committer"]["name"] == "GitHub" and commit_["commit"][
                "author"
            ]["name"] in (CMSSW_L1 + ["cmsbuild"]):
                head = commit_
                break

        if head is None:
            sys.exit(1)

        if not opts.dryRun:
            HEAD_SHA = create_git_tag(
                repo,
                RELEASE_NAME,
                head["sha"],
            )
        else:
            # Dummy SHA
            HEAD_SHA = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"

    tags = find_tags(repo, QUEUE + "_20")
    RELEASE_LIST = [
        t["ref"].replace("refs/tags/", "")
        for t in tags
        if t["object"]["sha"] == HEAD_SHA
    ]
    print(" ".join(RELEASE_LIST))
#!/usr/bin/env python

# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import os
import json
import sys
import urllib2


def get_env(name):
    env = os.environ.get(name)
    if not env:
        sys.stderr.write("ERROR: missing {}\n".format(name))
        sys.exit(2)
    return env


class Request(urllib2.Request):

    def __init__(self, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return self._method


def proxy_request(instance_name, method, path, body=None, headers=None):
    target = get_env("TSURU_TARGET").rstrip("/")
    token = get_env("TSURU_TOKEN")

    if not target.startswith("http://") and not target.startswith("https://"):
        target = "http://{}".format(target)

    url = "{}/services/proxy/{}?callback={}".format(target, instance_name,
                                                    path)

    if body:
        body = json.dumps(body)

    request = Request(method, url, data=body)
    request.add_header("Authorization", "bearer " + token)

    if headers:
        for header, value in headers.items():
            request.add_header(header, value)

    return urllib2.urlopen(request, timeout=30)


def add_url(name, url, expected_string=None):
    """
    add_url creates a new url checker, using the provided parameters. Usage:

        add-url <name> <url> [expected_string]

    expected_string is an optional parameter that represents the string that
    the healthcheck should expect to find in the body of the response. Example:

        tsuru {plugin-name} add-url mysite http://mysite.com/hc WORKING
    """
    data = {
        "name": name,
        "url": url,
    }
    if expected_string:
        data["expected_string"] = expected_string
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    proxy_request(name, "POST", "/url", data, headers)
    msg = "url {} successfully added!\n".format(url)
    sys.stdout.write(msg)


def remove_url(name, url):
    """
    remove_url removes the specified url checker. Usage:

        remove-url <name> <url>

    Example:

        tsuru {plugin-name} remove-url mysite http://mysite.com/hc
    """
    url = "/{}/url/{}".format(name, url)
    proxy_request(name, "DELETE", url)
    msg = "url {} successfully removed!\n".format(url)
    sys.stdout.write(msg)


def add_watcher(name, watcher):
    """
    add_watcher creates a new watcher
    """
    data = {
        "name": name,
        "watcher": watcher,
    }
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        "Accept": "text/plain"
    }
    proxy_request(name, "POST", "/watcher", data, headers)
    msg = "watcher {} successfully added!\n".format(watcher)
    sys.stdout.write(msg)


def remove_watcher(name, watcher):
    """
    remove_watcher creates a new watcher
    """
    url = "/{}/watcher/{}".format(name, watcher)
    proxy_request(name, "DELETE", url)
    msg = "watcher {} successfully removed!\n".format(watcher)
    sys.stdout.write(msg)


def command(command_name):
    commands = {
        "add-url": add_url,
        "remove-url": remove_url,
        "add-watcher": add_watcher,
        "remove-watcher": remove_watcher,
    }
    if command_name in commands:
        return commands[command_name]

    sys.stdout.write("Usage: tsuru <plugin> command [args]\n\n")
    sys.stdout.write("Available commands:\n")

    for name in commands.keys():
        sys.stdout.write("  {}\n".format(name))

    msg = "Use tsuru <plugin> help <commandname> to get more information."
    sys.stdout.write(msg)
    sys.exit(2)


def main(cmd, *args):
    command(cmd)(*args)


if __name__ == "__main__":
    main(sys.argv[1], *sys.argv[2:])

#!/usr/bin/python
"""Usage:
    check-consul-health.py node NODE DC
        [--addr=ADDR]
        [--CheckID=CheckID | --ServiceName=ServiceName]
        [--verbose]

Arguments:
    NODE  the consul node_name
    DC    the consul datacenter

Options:
    -h --help                  show this
    -v --verbose               verbose output
    --addr=ADDR                consul address [default: http://localhost:8500]
    --CheckID=CheckID          CheckID matcher
    --ServiceName=ServiceName  ServiceName matcher
"""
import argparse
import json
import traceback

try:
    import urllib.request as urllib
except ImportError:
    import urllib


def dump(it):
    if arguments['verbose']:
        print(it)


def build_node_url():
    url = "%(addr)s/v1/health/node/%(NODE)s?dc=%(DC)s" % arguments
    dump("Url: " + url)
    return url


def get_json_from_url(url):
    r = urllib.urlopen(url)
    response = r.read()
    dump("Response: " + str(response))
    dump("Status code: " + str(r.getcode()))

    return json.loads(response)


def print_check(check):
    print("> %(Node)s:%(ServiceName)s:%(Name)s:%(CheckID)s:%(Status)s" % check)


def process_failing(checks):
    def check_output(x):
        return x["Name"] + ":" + x["Output"]

    filters = map(lambda field: lambda x: arguments[field] is None or x[field] == arguments[field],
                  ['CheckID', 'ServiceName']
                  )

    filtered = list(filter(lambda x: all(f(x) for f in filters), checks))
    passing = list(filter(lambda x: x['Status'] == 'passing', filtered))
    warning = list(filter(lambda x: x['Status'] == 'warning', filtered))
    critical = list(filter(lambda x: x['Status'] == 'critical', filtered))

    if len(checks) == 0:
        print("There is no matching node!")
        return 1

    if len(filtered) == 0:
        print("There is no matching check!")
        return 1

    if len(critical):
        print("|".join(map(check_output, critical)))
        for check in critical:
            print_check(check)
    if len(warning):
        print("|".join(map(check_output, warning)))
        for check in warning:
            print_check(check)
    if len(passing):
        print("Passing: %d" % (len(passing)))
        for check in passing:
            print_check(check)

    return 2 if len(critical) else 1 if len(warning) else 0


def prepare_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Commands help', dest='node')
    node_parser = subparsers.add_parser('node')
    node_parser.add_argument('NODE', metavar='NODE', help='the consul node_name')
    node_parser.add_argument('DC', metavar='DC', help='the consul datacenter')
    node_parser.add_argument('--addr', default='http://localhost:8500',
                             help='consul address [default: http://localhost:8500]')
    node_parser.add_argument('--verbose', default=False, type=bool, help='verbose output')
    node_parser.add_argument('--CheckID', default=None, type=str, help='CheckID matcher')
    node_parser.add_argument('--ServiceName', default=None, type=str, help='ServiceName matcher')
    return parser.parse_args().__dict__


if __name__ == '__main__':
    try:
        arguments = prepare_args()

        url = build_node_url()
        json = get_json_from_url(url)
        exit(process_failing(json))
    except SystemExit:
        raise
    except:
        traceback.print_exc()
        exit(3)

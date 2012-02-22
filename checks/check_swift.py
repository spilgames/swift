#!/usr/bin/env python

import cloudfiles, pprint, pickle, StringIO, gzip, ConfigParser, signal, sys, os, time

pp = pprint.PrettyPrinter(indent=4)

config = ConfigParser.RawConfigParser()
config.read('/opt/admin/scripts/etc/swift-stats.conf')
# config.get(section, element)

username = config.get("stats", "username")
password = config.get("stats", "password")
authurl = config.get("stats", "authurl")
container_prefix = config.get("check", "container_prefix")
object_prefix = config.get("check", "object_prefix")

warn = False
warn_message = []

def delete_container(conn, container_name):
    container = conn.get_container(container_name)
    for obj in container.list_objects():
        container.delete_object(obj)
    del container
    conn.delete_container(container_name)

try:
    warn_threshold = float(sys.argv[1])
except:
    warn_threshold = 1

starttime = time.time()
try:
    conn = cloudfiles.get_connection(username, password, authurl=authurl)
except:
    print "CRITICAL - could not get authentication token"
    sys.exit(2)

for cont in conn.list_containers():
    if cont.startswith(container_prefix):
        if not warn:
            warn = True
            warn_message.append("found container %s - last run not cleaned up" %
                                cont)
        delete_container(conn, cont)

container_name = "%s_%d" % (container_prefix, starttime)
try:
    container = conn.create_container(container_name)
except:
    print "CRITICAL - could not create container"
    sys.exit(2)

try:
    file = container.create_object("%s_%s" % (object_prefix, starttime))
    file.write("test\n")
except:
    print "CRITICAL - could not write object"
    try:
        delete_container(conn, container_name)
    finally:
        sys.exit(2)

try:
    delete_container(conn, container_name)
except:
    print "CRITICAL - could not delete container"

delta = time.time() - starttime

if delta > warn_threshold:
    warn_message.append("Run took %f seconds (warning threshold is %f seconds)" %
                (delta, warn_threshold))
    warn = True

if warn:
    print "WARNING - " + " + ".join(warn_message) + " | 'TIME'=%fs" % delta
    sys.exit(1)

print "OK (%fs) | 'TIME'=%fs" % (delta, delta)

# pyZabbixSender
Python implementation of zabbix_sender.

*Take a look at the [wiki] page to get in deep details.*

This is a module that allows you to send data to a [Zabbix] server using Python. You don't need the zabbix_sender binary anymore.

Has been tested with Python 2.5.1 and 2.7

Python 2.5.1 doesn't have a json module (needed to implement zabbix protocol), so you can use [simplejson] instead.

Source code contains samples and comments to allows you start using it in no time. Here's a small example:
```python
# Creating a sender object
z = pyZabbixSender(server="zabbix-server", port=10051)

# Adding data (without timestamp)
z.addData(hostname="test_host", key="test_trap_1", value="12")
z.addData("test_host", "test_trap_2", "2.43")

# Adding data (with timestamp)
z.addData("test_host", "test_trap_2", "2.43", 1365787627)

# Ready to send your data?
results = z.sendData()

# Check if everything was sent as expected
if results[0][0] != z.RC_OK:
  print "oops!"

# Clear internal data to start populating again
z.clearData()

# Wants to send a single data point right now?
z.sendSingle("test_host","test_trap","12")
```

There are some more options, so take a look and discover how easy is to use it ;)


License
----

GNU GPLv2

[Zabbix]:http://www.zabbix.com/
[simplejson]:https://simplejson.readthedocs.org/en/latest/
[wiki]:https://github.com/kmomberg/pyZabbixSender/wiki

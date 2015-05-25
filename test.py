from pyZabbixSender import pyZabbixSender

# this import is optional. Here is used to create a timestamp to associate
# to some data points, for example/testing purposes only.
import time

# Specifying server, but using default port
z = pyZabbixSender("127.0.0.1")

def printBanner(text):
    border_char = '#'
    border = border_char * (len(text) + 4)
    print "\n\n%s" % border
    print "%s %s %s" % (border_char, text, border_char)
    print border
    
    
def test_01():
    '''
    Simple "debugging" usage example (using "sendDataOneByOne" method)
    '''
    printBanner("test_01")
    
    # Just ensuring we start without data, in case other example was
    # executed before this one
    z.clearData()

    # Adding a host/trap that exist
    z.addData("test_host", "test_trap", 21)

    # Adding a host that exist, but a trap that doesn't
    z.addData("test_host", "test_trap1", 100)

    # Sending stored data, one by one, to know which host/traps have problems
    results = z.sendDataOneByOne()

    # You'll get a "results" like:
    #[ (0, {'host': 'test_host', 'value': 21, 'key': 'test_trap'})
    #  (1, {'host': 'test_host', 'value': 100, 'key': 'test_trap1'})
    #]
    print "---- Results content:"
    print results
        
    # What if we want to remove data already sent, and retry or do something
    # else with the data no sent?
    print "\n---- Data before the cleaning:\n%s\n" % str(z)
    for (code, data_point) in results:
        if code != z.RC_OK:
            print "Failed to send: %s" % str(data_point)
        else:
            # This data_point was successfully sent, so we can remove from internal data
            z.removeDataPoint(data_point)
    print "\n---- Data after the cleaning:\n%s\n" % str(z)
    
    # at this point you can even retry sending the data calling the "sendDataOneByOne"
    # or "sendData" methods 

    
def test_02():
    '''
    Testing "max_data_per_conn" parameter in "sendData" method
    '''
    printBanner("test_02")
    
    # Just ensuring we start without data, in case other example was
    # executed before this one
    z.clearData()

    # Adding some valid data
    for i in range (10):
        z.addData("test_host", "test_trap", i)
        
    # Now adding a trap that doesn't exist in the server
    z.addData("test_host", "test_trap1", 3)
    
    results = z.sendData(max_data_per_conn=3)
    
    # Now lets take a look at the return. Should be something like this:
    #[ (0, {u'info': u'Processed 3 Failed 0 Total 3 Seconds spent 0.000062', u'response': u'success'}),
    #  (0, {u'info': u'Processed 3 Failed 0 Total 3 Seconds spent 0.000057', u'response': u'success'}),
    #  (0, {u'info': u'Processed 3 Failed 0 Total 3 Seconds spent 0.000056', u'response': u'success'}),
    #  (1, {u'info': u'Processed 1 Failed 1 Total 2 Seconds spent 0.000041', u'response': u'success'})]
    print results


def test_03():
    '''
    Testing method "sendSingle"
    '''
    printBanner("test_03")

    # We don't need to clean internal data, because we'll send data given to the method
    
    # Sending data right now, without timestamp
    result = z.sendSingle("test_host", "test_trap", 1)
    
    print "---- After sendSingle without timestamp"
    print result
    
    # Now sending data with timestamp
    result = z.sendSingle("test_host", "test_trap", 1, int(round(time.time())))
    print "\n---- After sendSingle with timestamp"
    print result
    

def test_04():
    '''
    Testing getData method.
    '''
    printBanner("test_04")
    
    # Just ensuring we start without data, in case other example was
    # executed before this one
    z.clearData()
    
    # Adding data
    z.addData("test_host", "test_trap", 1)
    z.addData("test_host", "test_trap", 2)
    
    # Showing current data
    print "---- Showing stored data:"
    print z
    
    # remember that getData returns a copy of the data
    copy_of_data = z.getData()
    print "\n---- Showing data returned:"
    print copy_of_data
    
    # We'll modify returned data, to show this won't affect internal data
    print "\n---- Modifying returned data"
    copy_of_data.append({'host': 'test_host', 'value': 500, 'key': 'test_trap'})

    # Showing current data
    print "\n---- Showing stored data again (note is the same as before):"
    print z

    print "\n---- Showing returned and modified data:"
    print copy_of_data
    
    
        
# Here you can execute the test/examples you want
test_01()
test_02()
test_03()
test_04()
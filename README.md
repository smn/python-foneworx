# Houston

Twisted based library for interacting with Foneworx.co.za's XML API

# Methods implemented

* Login
* Logout
* NewMessages
* DeleteNewMessages
* SendMessages
* SentMessages
* DeleteSentMessages

# Usage:

It runs in Twisted, uses Trial for unittests.

    $ virtualenv --no-site-packages ve
    $ source ve/bin/activate

Run the client tests, the responses for these are mocked and do not need
a Foneworx account set up.

    (ve)$ trial tests.client_tests

Run the connection tests, these tests do actually connect to Foneworx to send & receive SMSs. Running these tests will cost you money / SMS credits.

    (ve)$ MSISDN=+27xxx USERNAME=xxx PASSWORD=xxx trial tests.connection_tests

Part of the tests is a full stack: receive, reply, delivery report & delete.

    (ve)$ USERNAME=xxx PASSWORD=xxx trial \
    > tests.connection_tests.HoustonConnectionTestCase.test_full_stack
    tests.connection_tests
      HoustonConnectionTestCase
        test_full_stack ... Please send a test SMS to Foneworx in order to fill the inbox.
    Checking for new SMSs every 2 seconds
    Checking for new SMSs every 2 seconds
    Checking for new SMSs every 2 seconds
    Checking for new SMSs every 2 seconds
    Replying to an SMS received from +27xxxxxxxxx
    Waiting until delivered
    Not delivered yet: At Network
    Not delivered yet: At Network
    Not delivered yet: At Network
    Delivered!
    Deleting the received message
    Deleted: Success
    Deleting the sent message
    Deleted: None
    Logging out
    Logged out: Success
                                               [OK]
    
    --------------------------------------------------
    Ran 1 tests in 51.191s
    
    PASSED (successes=1)
    
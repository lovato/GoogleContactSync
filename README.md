GoogleContactSync
=================

The provided *ContactBroker* class has several methods to help with contact management between Google Accounts.

Currently, the following is supported:
 * Copying contacts between accounts
 * Moving contacts between accounts
 * Adding contacts
 * Deleting contacts
 * Performing one-way contact sync between two accounts
 * Performing multi-way sync between any number of accounts

One-way and multi-way sync both automatically find and merge duplicate contacts.

*ContactBroker.py* contains docstrings for each function. *GoogleContactSync.py* contains example instantiation of the broker.

**Don't forget to edit *settings.py* and add accounts as needed.**

Dependencies
------------
 * [GData API Python Wrapper](http://code.google.com/p/gdata-python-client/downloads/list)

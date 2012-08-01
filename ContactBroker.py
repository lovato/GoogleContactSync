import gdata.contacts.data
import gdata.contacts.client

from GCSHelpers import ceIsOrigin, ceMerge, ceCmp, ceFindDuplicates, ceMergeDuplicates

class ContactBroker:
	def __init__(self, google_accounts, app_name):
		self.appname = app_name
		self.accounts = {}
		self.client = None
		self.batch_queue = gdata.contacts.data.ContactsFeed()
		
		for account in google_accounts:
			self.accounts[account.nickname] = account
			try:
				client = gdata.contacts.client.ContactsClient(source=app_name)
				client.ClientLogin(account.email, account.pwd, client.source)
				self.accounts[account.nickname].client = client
			except Exception as e:
				print "Error connecting account '%s': %s" % (account.nickname, e)
				del self.accounts[account.nickname]
		
		if len(self.accounts) == 0:
			print "Could not connect any accounts, exiting"
			exit()
		
		self.current_account = self.accounts.itervalues().next()
		self.client = self.current_account.client
		
		print "Account '%s' currently selected" % self.current_account.nickname
	
	def GetAccountList(self):
		"""List the currently connected accounts
		
		Args:
			None
		Returns:
			List of account nicknames
			
		"""
		return self.accounts.keys()
	
	def SelectAccount(self, nickname):
		"""Select an account and set it as the current 'working' account
		Calling this method also cleares the Batch Queue, if it isn't empty
		
		Args:
			nickname: A string corresponding to an account nickname set in settings.py
		Returns:
			A boolean value - True was successful, False was unsuccessful
		"""
		self.ClearBatchQueue()
		
		if nickname in self.accounts:
			self.current_account = self.accounts[nickname]
			self.client = self.current_account.client
			return True
		else:
			return False
	
	def ClearBatchQueue(self):
		"""Clear the batch queue"""
		self.batch_queue = gdata.contacts.data.ContactsFeed()
	
	def BatchEnqueue(self, action, contact):
		"""Add an action to the batch queue
		
		Args:
			action: 'retrieve', 'create', 'update', or 'delete'
			contact: The ContactEntry object to perform the action on
		"""
		
		if action == 'retrieve':
			self.batch_queue.AddQuery(entry=contact, batch_id_string='retrieve')
		elif action == 'create':
			contact.group_membership_info = [gdata.contacts.data.GroupMembershipInfo(href=self.GetFirstGroupId())]
			self.batch_queue.AddInsert(entry=contact, batch_id_string='create')
		elif action == 'update':
			self.batch_queue.AddUpdate(entry=contact, batch_id_string='update')
		elif action == 'delete':
			self.batch_queue.AddDelete(entry=contact, batch_id_string='delete')
	
	def ExecuteBatchQueue(self):
		"""Execute all actions in the batch queue"""
		self.client.ExecuteBatch(self.batch_queue, 'https://www.google.com/m8/feeds/contacts/default/full/batch')
		self.ClearBatchQueue();
	
	##
	# Note: Methods below this point act on the currently selected account
	##
	
	def GetContactList(self):
		"""Get a list of all the contacts from the currently selected account
		
		Args:
			None
		Returns:
			A list of gdata.contacts.data.ContactEntry objects from the selected account
		"""
		feeds = []
		feed = self.client.GetContacts()
		feeds.append(feed)
		next = feed.GetNextLink()
		while next:
			feed = self.client.GetContacts(uri=next.href)
			feeds.append(feed)
			next = feed.GetNextLink()
		
		contacts = []
		for feed in feeds:
			if not feed.entry:
				continue
			else:
				for i, entry in enumerate(feed.entry):
					contacts.append(entry)
		return contacts
	
	def GetFirstGroupId(self):
		"""Lazily get the first contact group's Atom Id
		
		Args:
			None
		Returns:
			The Group
		"""
		return self.client.GetGroups().entry[0].id.text
		
			
	def AddContact(self, contact):
		"""Add a contact to the selected account
		
		Args:
			contact: A gdata.contacts.data.ContactEntry instance to add
		Returns:
			None
		"""
		contact.group_membership_info = [gdata.contacts.data.GroupMembershipInfo(href=self.GetFirstGroupId())]
		try:
			self.client.CreateContact(contact)
		except gdata.client.RequestError:
			pass
	
	def RemoveContact(self, contact):
		"""Remove a contact from the selected account
		
		Args:
			contact: A gdata.contacts.data.ContactEntry instance to remove
		Returns:
			None
		"""
		self.client.Delete(contact)
	
	def RemoveAll(self):
		"""Remove all contacts from the selected account
		
		Args:
			None
		Returns:
			None
		"""
		contacts = self.GetContactList()
		
		for contact in contacts:
			self.BatchEnqueue('delete', contact)
		self.ExecuteBatchQueue()
	
	def MergeContacts(self, contact1, contact2):
		"""Merges two contacts
		
		Args:
			contact1: First ContactEntry object
			contact2: Second ContactEntry object
		Returns:
			None
		"""
		contact3 = ceMerge(contact1, contact2)
		
		self.BatchEnqueue('update', contact3)
		self.BatchEnqueue('delete', contact2)
		self.ExecuteBatchQueue()
	
	def FindAndMergeDuplicates(self):
		pass
	
	##
	# Methods below this point act on all connected accounts
	##
	
	def CopyContacts(self, from_nickname, to_nickname):
		"""Copy all contacts from one account to another
		This method does not check for duplicates
		
		Args:
			from_nickname: Account nickname to copy from
			to_nickname: Account nickname to copy to
		Returns:
			None
		"""
		self.SelectAccount(from_nickname)
		contacts = self.GetContactList()
		
		self.SelectAccount(to_nickname)
		for contact in contacts:
			self.BatchEnqueue('create', contact)
		self.ExecuteBatchQueue()
		
	def MoveContacts(self, from_nickname, to_nickname):
		"""Move all contacts from one account to another
		This method does not check for duplicates
		
		Args:
			from_nickname: Account nickname to move from
			to_nickname: Account nickname to move to
		Returns:
			None
		"""
		self.SelectAccount(from_nickname)
		contacts = self.GetContactList()
		
		# Copy contacts -before- deleting
		self.SelectAccount(to_nickname)
		for contact in contacts:
			self.BatchEnqueue('create', contact)
		self.ExecuteBatchQueue()
		
		# Then delete
		self.SelectAccount(from_nickname)
		for contact in contacts:
			self.BatchEnqueue('delete', contact)
		self.ExecuteBatchQueue()
	
	def OneWaySync(self, from_nickname, to_nickname):
		"""Perform a one-way sync: from_nickname --> to_nickname
		This method checks for duplicates. Contacts in 'from_account' with a duplicate in 'to_account' will be merged together and saved in 'to_account.
		
		Args:
			from_nickname: Account nickname to sync from
			to_nickname: Account nickname to sync to
		Returns:
			None
		"""
		contacts = []
		self.SelectAccount(from_nickname)
		from_contacts = self.GetContactList()
		self.SelectAccount(to_nickname)
		to_contacts = self.GetContactList()
		from_contacts.extend(to_contacts)
		
		duplicates, contacts = ceFindDuplicates(from_contacts)
		
		merged, todelete = ceMergeDuplicates(duplicates)
		
		# contacts: non-duplicate contacts
		# merged: merged duplicate contacts
		# todelete: duplicates to delete
		
		for contact in todelete:
			if ceIsOrigin(contact, self.current_account.email):
				self.BatchEnqueue('delete', contact)
		self.ExecuteBatchQueue()
		
		self.SelectAccount(to_nickname)
		for contact in contacts:
			if not ceIsOrigin(contact, self.current_account.email):
				self.BatchEnqueue('create', contact)
		self.ExecuteBatchQueue()
		
		for contact in merged:
			if ceIsOrigin(contact, self.current_account.email):
				self.BatchEnqueue('update', contact)
			else:
				self.BatchEnqueue('create', contact)
		self.ExecuteBatchQueue()
	
	def MultiWaySync(self, accounts):
		"""Perform a multi-way sync between given accounts
		
		Args:
			accounts: List of account nicknames to sync between
		Returns:
			None
		"""
		cleaned_contacts = []
		contacts = []
		
		for account in accounts:
			self.SelectAccount(account)
			contacts.extend(self.GetContactList())
		
		duplicates, originals = ceFindDuplicates(contacts)
		merged, todelete = ceMergeDuplicates(duplicates)
		
		cleaned_contacts.extend(originals)
		cleaned_contacts.extend(merged)
		
		for account in accounts:
			self.SelectAccount(account)
			self.RemoveAll()
		
		for account in accounts:
			self.SelectAccount(account)
			for contact in cleaned_contacts:
				self.BatchEnqueue('create', contact)
			self.ExecuteBatchQueue()

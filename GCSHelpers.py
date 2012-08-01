from urllib import quote, unquote

class GoogleAccount:
	def __init__(self, nickname, email, pwd):
		self.nickname = nickname
		self.email = email
		self.pwd = pwd
		self.client = None

def ceCmp(contact1, contact2):
	"""Compare two ContactEntry objects by first and last name
	
	Args:
		contact1: First ContactEntry object
		contact2: Second ContactEntry object
	Returns:
		A boolean value. True if the two names match, False if the two names do not match
	"""
	if contact1.name is None or contact2.name is None:
		return contact1.name is contact2.name
	else:
		if contact1.name.given_name is None or contact2.name.given_name is None:
			if contact1.name.family_name is None or contact2.name.family_name is None:
				return contact1.name.given_name is contact2.name.given_name and contact1.name.family_name is contact2.name.family_name
			else:
				return contact1.name.given_name is contact2.name.given_name and contact1.name.family_name.text.lower() == contact2.name.family_name.text.lower()
		else:
			if contact1.name.family_name is None or contact2.name.family_name is None:
				return contact1.name.given_name.text.lower() == contact2.name.given_name.text.lower() and contact1.name.family_name is contact2.name.family_name
			else:
				return contact1.name.given_name.text.lower() == contact2.name.given_name.text.lower() and contact1.name.family_name.text.lower() == contact2.name.family_name.text.lower()
				

def ceMerge(contact1, contact2):
	"""Merge two ContactEntry objects together. The second contact's information that is not contained in the first contact is copied to the first contact, and the modified contact is returned.
	
	Args:
		contact1: First ContactEntry object
		contact2: Second ContactEntry object
	Retruns:
		A ContactEntry object representing the two merged contacts
	"""
	
	# Copy anything contact1 doesn't have
	for atb, val in vars(contact1).iteritems():
		if val in [None, [], {}]:
			setattr(contact1, atb, getattr(contact2, atb))
	
	# Copy new items from lists
	for atb, val in vars(contact2).iteritems():
		if type(val) == list:
			if atb == 'group_membership_info':
				if ceOrigin(contact1) != ceOrigin(contact2):
					continue
			vals = getattr(contact1, atb)
			for item in val:
				if item not in vals:
					if hasattr(item, 'primary'):
						setattr(item, 'primary', False)
					vals.append(item)
			setattr(contact1, atb, vals)
	return contact1

def ceFindDuplicates(contacts):
	"""Find duplicates within a list of contacts
	
	Args:
		contacts: A list of ContactEntry objects to search
	Returns:
		A list of lists. Each list contains entries determined to be duplicates of each other.
	"""
	sets = []
	nondups = []
	while len(contacts):
		duplicates = [contacts.pop()]
		temp = contacts
		for contact in temp:
			if ceCmp(duplicates[0], contact):
				duplicates.append(contact)
				contacts.remove(contact)
		if len(duplicates) > 1:
			sets.append(duplicates)
		else:
			nondups.append(duplicates[0])
	return sets, nondups

def ceMergeDuplicates(sets):
	"""Merge duplicate sets of contacts
	
	Args:
		sets: A list of lists, where each list contains duplicate contacts to be merged
	Returns:
		A list of resulting contacts
		A list of contacts to be deleted
	"""
	contacts = []
	todelete = []
	
	for duplicates in sets:
		contact = duplicates.pop(0)
		while len(duplicates):
			duplicate = duplicates.pop(0)
			contact = ceMerge(contact, duplicate)
			todelete.append(duplicate)
		contacts.append(contact)
	
	return contacts, todelete

def ceIsOrigin(contact, email):
	"""Returns whether or not the contact's originating account matches the given email
	
	Args:
		contact: A ContactEntry object
		email: An email to check against
	Return:
		A boolean value. True if contact's origin is email, otherwise False
	"""
	return quote(email) in contact.id.text

def ceOrigin(contact):
	"""Returns the contact's origin email
	
	Args:
		contact: A ContactEntry object
	Return:
		A string containing the email
	"""
	return contact.id.text.split("/")[6]
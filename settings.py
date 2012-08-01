from GCSHelpers import GoogleAccount

app_name = "GoogleContactSync"

google_accounts = [
	GoogleAccount(
		nickname= 'Nickname1', # A nickname to identify this account
		email= 'user@domain1.com', # Google account email
		pwd= 'password' # Google account password
	),
	GoogleAccount(
		nickname= 'Nickname2',
		email= 'user@domain2.com',
		pwd= 'password'
	)
]
import urllib2
import hashlib
import datetime
import webbrowser
import json
import time

# supported Facebook API methods
# keys   = instance methods
# values = actual Facebook methods
FB_METHODS = {
	'create_token': 'auth.createToken',
	'get_session_info': 'auth.getSession',
	'get_friends': 'friends.get',
	'get_status': 'status.get',
	'get_app_users': 'friends.getAppUsers',
	'get_logged_in_user': 'users.getLoggedInUser',
	'get_user_info': 'users.getInfo',
}

class Facebook():
	"""
	This is a Facebook Connect API wrapper that tries to be as
	up to date and as SIMPLE as possible.
	After spending countless hours trying to find a decent
	Facebook Python library with little (and eventually no) luck,
	I decided to write my own.
	"""
	
	def __init__(self, api_key=None, secret_key=None, session_key=None, uid=None, format='JSON', v='1.0'):
		"""Provide initial values"""
		#if api_key is None or secret_key is None:
		#	raise Exception("The API and secret keys are required: Facebook(api_key, secret_key)")
		# The following keys are for FratMusic's Facebook app.
		self.API_KEY = api_key or '3d308515ca9208a744331d417050ed5f'
		self.SECRET_KEY = secret_key or '89c415411bafa4b1379304754f3dbd0a'
		self.API_VERSION = str(v)
		self.FORMAT = str(format)
		self.AUTH_TOKEN = None
		self.SESSION_KEY = session_key
		self.SESSION_EXPIRATION = None
		self.UID = uid
		self.FRIENDS = None
		self.IS_AUTHORIZED = False
		
		self.COMMON_PARAMS = {
			'api_key': self.API_KEY,
			'v': self.API_VERSION,
			'format': self.FORMAT,
		}
	
	def create_token(self):
		"""
		This method is for desktop applications. Created for easy testing.
		Requesting an authorization token from Facebook.
		For web apps, open the login url with a query string of the API key:
		http://www.facebook.com/login.php?api_key=<YOUR API KEY>
		You can add a 'next' parameter that is relavent to the Facebook
		Connect base url. Example:
		Facebook Connect base URL = http://domain.com/
		Login = facebook.com/login.php?api_key=<key>&next=post/auth/
		This will redirect the user to domain.com/post/auth/ after
		signing in successfully.
		See open_login_url() for more information.
		"""
		params = {
			'method': FB_METHODS['create_token'],
		}
		params.update(self.COMMON_PARAMS)		
		response = self.send_request(params)
		self.AUTH_TOKEN = response
		return response
	
	def open_login_url(self, auth_token=None, next=None, popup=True):
		"""
		Opens the web browser to let the user log in and authenticate the
		app with the given auth_token.
		"""
		url = 'http://www.facebook.com/login.php?'
		url += 'api_key=' + self.API_KEY
		url += '&auth_token=' + (auth_token or self.AUTH_TOKEN)
		if next:
			url += '&next=' + next
		if popup:
			url += '&popup=1'
		webbrowser.open(url)
	
	def get_login_url(self, popup=True, next=None):
		"""
		For web apps.
		Opens the Facebook login page to let the user log into
		the app using their Facebook account.
		"""
		url = 'http://www.facebook.com/login.php?api_key=' + self.API_KEY
		if popup:
			url += '&popup=1'
		if next:
			url += '&next=' + next
		return url
	
	def get_session_info(self, auth_token=None):
		"""
		Lets user log into Facebook with the auth token.
		If the auth_token parameter is provided, it will be used and
		it will be saved in self.AUTH_TOKEN (for future use).
		Returns session information (session key, uid, expiration).
		"""
		if auth_token:
			self.AUTH_TOKEN = auth_token
		
		params = {
			'auth_token': self.AUTH_TOKEN,
			'method': FB_METHODS['get_session_info'],
		}
		params.update(self.COMMON_PARAMS)		
		session_info = self.send_request(params)
		
		self.SESSION_KEY = session_info['session_key']
		self.SESSION_EXPIRATION = session_info['expires']
		self.UID = session_info['uid']
		self.IS_AUTHORIZED = True
		return session_info
	
	def get_friends(self, session_key=None, uid=None):
		"""
		Get a user's friends.
		Provide either a session key or a UID.
		If both are provided, session key will be used and UID will be ignored.
		"""
		if self.FRIENDS:
			return self.FRIENDS
		
		params = {
			'call_id': int(time.time() * 1000000),
			'session_key': self.SESSION_KEY,
			'method': FB_METHODS['get_friends'],
		}
		params.update(self.COMMON_PARAMS)		
		response = self.send_request(params)
		self.FRIENDS = response
		return response
	
	def get_status(self, limit=10):
		"""
		Returns the last <limit> status updates for the current user.
		"""
		params = {
			'call_id': int(time.time() * 1000000),
			'session_key': self.SESSION_KEY,
			'method': FB_METHODS['get_status'],
			'limit': limit,
		}
		params.update(self.COMMON_PARAMS)		
		response = self.send_request(params)
		return response
	
	def get_app_users(self):
		"""
		http://wiki.developers.facebook.com/index.php/Friends.getAppUsers
		Returns friends of current user who authorized this app too.
		"""
		params = {
			'session_key': self.SESSION_KEY,
			'call_id': int(time.time() * 1000000),
			'method': FB_METHODS['get_app_users'],
		}
		params.update(self.COMMON_PARAMS)
		response = self.send_request(params)
		return response
	
	def get_logged_in_user(self):
		"""
		http://wiki.developers.facebook.com/index.php/Users.getLoggedInUser
		Returns the UID of the currently logged in user via the session key.
		Note that the UID is stored in self.UID when the session is first
		retrieved from Facebook.
		This method is useful is you still have the session key, but lost
		the user ID.
		"""
		params = {
			'session_key': self.SESSION_KEY,
			'call_id': int(time.time() * 1000000),
			'method': FB_METHODS['get_logged_in_user'],
		}
		params.update(self.COMMON_PARAMS)
		response = self.send_request(params)
		self.UID = response
		self.IS_AUTHORIZED = True
		return response
	
	def get_uid(self):
		"""
		Get the cached UID or fetch it from Facebook using the session key.
		"""
		return self.UID or self.get_logged_in_user()
	
	def is_authorized(self):
		"""
		Checks whether the current instance is bound to a user.
		Returns True if self.UID and self.SESSION_KEY are set, False otherwise.
		"""
		return self.IS_AUTHORIZED
	
	def get_user_info(self, uids=None, fields=None):
		"""
		http://wiki.developers.facebook.com/index.php/Users.getInfo
		Returns a wide range of user related information.
		uids:
			A list of strings representing user IDs:
			('user_id_1', 'user_id_2', ...)
		fields:
			A list of strings representing user fields:
			('first_name', 'last_name', 'email', ...)
		"""
		params = {
			'api_key': self.API_KEY,
			'call_id': int(time.time() * 1000000),
			'method': FB_METHODS['get_user_info'],
		}
		if uids:
			params.update({'uids': ','.join([str(uid) for uid in uids])})
		else:
			params.update({'uids': self.get_uid()})
		
		if fields:
			params.update({'fields': ','.join(fields)})
		else:
			params.update({'fields': 'first_name,last_name,name,email'})
		
		params.update(self.COMMON_PARAMS)
		response = self.send_request(params)
		return response
	
	def get_potential_users(self):
		"""
		Gets the user's friends who have not authorized the app.
		Returns a list of user IDs.
		"""
		app_users = self.get_app_users()
		friends = self.get_friends()
		potential_users = [uid for uid in friends if uid not in app_users]
		return potential_users
	
	def sort_and_create_signature(self, params):
		"""
		Sort the given parameters and create a signature.
		Returns a two-item tuple: (<signature>, <sorted parameters>).
		<sorted params> can be used directly in a URL. For example:
		request = 'http://api.facebook.com/restserver.php?' + <sorted params>
		"""
		arg_list = [(key, params[key]) for key in params.keys()]
		sorted_list = sorted(arg_list)
		raw_values = usable_sorted_params = ''
		for key, value in sorted_list:
			raw_values += key + '=' + str(value)
			usable_sorted_params += '&' + key + '=' + str(value)
		raw_values += self.SECRET_KEY
		signature = hashlib.md5(raw_values).hexdigest()
		return usable_sorted_params + '&sig=' + signature
	
	def send_request(self, params):
		"""
		Sends a request to Facebook's REST API server.
		params:
			The request parameters including the signature.
		"""
		sorted_params = self.sort_and_create_signature(params)
		url = 'http://api.facebook.com/restserver.php?' + sorted_params
		request = urllib2.Request(url)
		request.add_header('Content-Type', 'application/x-www-form-urlencoded')
		request.add_header('method', 'POST')
		opener = urllib2.build_opener()
		response = opener.open(request).read()
		encoded_response = json.loads(str(response))
		# check for errors in response
		if 'error_code' in str(encoded_response):
			error_code = int(encoded_response['error_code'])
			return error_code
		return encoded_response

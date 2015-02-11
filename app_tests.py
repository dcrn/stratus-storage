import app, json, unittest

class StorageTestCase(unittest.TestCase):
	def setUp(self):
		app.app.config['TESTING'] = True
		self.app = app.app.test_client()
		self.username = 'dcrn'
		self.repository = 'testrepo'
		self.access_token = 'c5a78551cb5c6a19d04b04bbd5fbee66ffe8e3c3'

	def test_git_init_delete(self):
		test_url = self.username + '/' + self.repository
		test_remote = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'

		# Check repo doesn't exist
		re = self.app.get(test_url)
		assert re.status_code == 404 # Not Found

		# Create repo
		re = self.app.post(test_url, 
			data=json.dumps({
					test_remote_name: test_remote
				})
			)
		assert re.status_code == 201 # Created

		# Confirm repo exists
		re = self.app.get(test_url)
		j = json.loads(str(re.data, 'utf-8'))
		assert re.status_code == 200
		assert j[test_remote_name] == test_remote

		# Delete repo
		re = self.app.delete(test_url)
		assert re.status_code == 200

		# Confirm deletion
		re = self.app.get(test_url)
		assert re.status_code == 404 # Not Found

	def test_git_clone(self):
		test_url_repo = self.username + '/' + self.repository
		test_url_clone = test_url_repo + '/clone'
		test_remote = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'

		"""
		# Create repo
		re = self.app.post(test_url_repo, 
			data=json.dumps({
					test_remote_name: test_remote
				})
			)
		assert re.status_code == 201 # Created

		# Clone
		re = self.app.get(test_url_clone, 
			args={'access_token': self.access_token})
		assert re.status_code == 200
		"""

	def test_git_status(self):
		pass

	def test_git_commit(self):
		pass

	def test_git_pull(self):
		pass

	def test_git_push(self):
		pass
		
	def test_file(self):
		test_url = self.username + '/' + self.repository + '/file/test.txt'
		test_data_a = 'Testing 123'
		test_data_b = 'foobar'

		# Get non-existant file
		re = self.app.get(test_url)
		assert re.status_code == 404

		# Create new file without submitting any data
		re = self.app.post(test_url)
		assert re.status_code == 400

		# Create new file
		re = self.app.post(test_url, 
			data=json.dumps({'data':test_data_a}))
		assert re.status_code == 201

		# Confirm data stored in file
		re = self.app.get(test_url)
		assert re.status_code == 200
		assert json.loads(str(re.data, 'utf-8'))['data'] == test_data_a

		# Update file
		re = self.app.put(test_url, 
			data=json.dumps({'data':test_data_b}))
		assert re.status_code == 200

		# Confirm file updated
		re = self.app.get(test_url)
		assert re.status_code == 200
		assert json.loads(str(re.data, 'utf-8'))['data'] == test_data_b

		# Delete file
		re = self.app.delete(test_url)
		assert re.status_code == 200

		# Confirm deleted
		re = self.app.get(test_url)
		assert re.status_code == 404
		
	def test_tree(self):
		test_url_repo = self.username + '/' + self.repository
		test_url_tree = test_url_repo + '/tree'

		"""
		# Get tree of repo
		re = self.app.get(test_url)
		j = json.loads(str(re.data, 'utf-8'))
		assert len(j) == 0
		"""

if __name__ == '__main__':
	unittest.main()
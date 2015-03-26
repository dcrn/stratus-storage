import application, json, unittest, time, random, string

class StorageTestCase(unittest.TestCase):
	def setUp(self):
		application.app.config['TESTING'] = True
		self.app = application.app.test_client()

		# Perform the unit tests on this user and repository, using the specified access token
		self.username = 'dcrn'
		self.repository = 'test-repo'
		self.access_token = 'c5a78551cb5c6a19d04b04bbd5fbee66ffe8e3c3'

	def test_git_init_delete(self):
		test_url = self.username + '/' + self.repository
		test_remote = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url)
		assert re.status_code in [200, 404]

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
		assert re.status_code == 200
		j = json.loads(str(re.data, 'utf-8'))
		assert j['remotes'][test_remote_name] == test_remote

		# Delete repo
		re = self.app.delete(test_url)
		assert re.status_code == 200

		# Confirm deletion
		re = self.app.get(test_url)
		assert re.status_code == 404 # Not Found

	def test_git_status(self):
		test_file_a = 'subdir/hello.txt'
		test_file_b = 'README.md'
		test_data = 'foobar'
		test_remote_url = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'
		test_url_repo = self.username + '/' + self.repository
		test_url_pull = test_url_repo + '/pull/' + test_remote_name
		test_url_file_a = test_url_repo + '/file/' + test_file_a
		test_url_file_b = test_url_repo + '/file/' + test_file_b
		test_url_status = test_url_repo + '/status'

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Init local repo with remote
		re = self.app.post(test_url_repo, 
			data=json.dumps({test_remote_name: test_remote_url}))
		assert re.status_code == 201 # Created

		# Get status before pull
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK

		# Pull repo
		re = self.app.post(test_url_pull)
		assert re.status_code == 200 # OK
		
		# Check status, should have no changes
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j == {'R': [], 'U': [], 'M': [], 'A': [], 'D': []}

		# Create test file
		re = self.app.post(test_url_file_a,
			data=json.dumps({'data': test_data}))
		assert re.status_code == 201 # Created

		# Should now have 1 untracked file
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j == {
			'R': [], 'U': [test_file_a], 
			'M': [], 'A': [], 'D': []}

		# Change contents of README.md
		re = self.app.put(test_url_file_b,
			data=json.dumps({'data': test_data}))
		assert re.status_code == 200 # OK

		# Check that README.md is modified
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j == {
			'R': [], 'U': [test_file_a], 
			'M': [{'A': test_file_b, 'B': test_file_b}],
			'A': [], 'D': []}

		# Delete README.md
		self.app.delete(test_url_file_b)
		assert re.status_code == 200 # OK

		# Check deleted status
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j == {
			'R': [], 'U': [test_file_a], 'M': [],
			'A': [], 'D': [{'A': test_file_b}]}

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK

	def test_git_commit(self):
		test_file_a = 'subdir/hello.txt'
		test_file_b = 'README.md'
		test_data = 'foobar'
		test_remote_url = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'
		test_url_repo = self.username + '/' + self.repository
		test_url_pull = test_url_repo + '/pull/' + test_remote_name
		test_url_commit = test_url_repo + '/commit'
		test_url_file_a = test_url_repo + '/file/' + test_file_a
		test_url_file_b = test_url_repo + '/file/' + test_file_b
		test_url_status = test_url_repo + '/status'

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Init local repo with remote
		re = self.app.post(test_url_repo, 
			data=json.dumps({test_remote_name: test_remote_url}))
		assert re.status_code == 201 # Created

		# Get repo info, make sure head is null
		re = self.app.get(test_url_repo)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['head'] == None
		assert j['remotes'][test_remote_name] == test_remote_url

		# Pull repo
		re = self.app.post(test_url_pull)
		assert re.status_code == 200 # OK

		# Get head commit hash
		re = self.app.get(test_url_repo)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['head'] is not None
		head = j['head']

		# Add a new file 'hello.txt'
		re = self.app.post(test_url_file_a, 
			data=json.dumps({'data': test_data}))
		assert re.status_code == 201 # Created

		# Modify README.md
		re = self.app.put(test_url_file_b, 
			data=json.dumps({'data': test_data}))
		assert re.status_code == 200 # OK

		# Get status, file_a should be untracked and 
		# file_b should be modified
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j == {
			'R': [], 'U': [test_file_a], 
			'M': [{'A': test_file_b, 'B': test_file_b}],
			'A': [], 'D': []}

		# Commit files
		re = self.app.post(test_url_commit,
			data=json.dumps({
					'A': [test_file_a, test_file_b], 
					'R': [], 
					'msg': 'Unittest ' + time.strftime("%c"),
					'name': 'Unit Tests',
					'email': 'UnitTests@gmail.com'
				}))
		assert re.status_code == 200 # OK

		# Confirm head changed
		re = self.app.get(test_url_repo)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['head'] is not head
		
		# Check status, should have no changes
		re = self.app.get(test_url_status)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j == {'R': [], 'U': [], 'M': [], 'A': [], 'D': []}

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK


	def test_git_pull(self):
		test_file = 'README.md' # Already in repo
		test_data = 'hello world\n' # Contents of test_file
		test_remote_url = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'
		test_url_repo = self.username + '/' + self.repository
		test_url_pull = test_url_repo + '/pull/' + test_remote_name
		test_url_file = test_url_repo + '/file/' + test_file

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Pull non-existant repo
		re = self.app.post(test_url_pull)
		assert re.status_code == 404 # Not Found

		# Init local repo with remote
		re = self.app.post(test_url_repo, 
			data=json.dumps({test_remote_name: test_remote_url}))
		assert re.status_code == 201 # Created

		# Get repo info
		re = self.app.get(test_url_repo)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['head'] == None

		# Attempt to pull the repo
		re = self.app.post(test_url_pull)
		assert re.status_code == 200 # OK

		# Confirm that the head ref changed
		re = self.app.get(test_url_repo)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['head'] is not None

		# Confirm the contents of the repo
		re = self.app.get(test_url_file)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['data'] == test_data

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK

	def test_git_push(self):
		filename_len = 14
		filedata_len = 32

		# Generate random data to be pushed
		test_file = ('').join(random.choice(string.ascii_lowercase) for n in range(filename_len)) + '.txt'
		test_data = ('').join(random.choice(string.ascii_lowercase) for n in range(filedata_len))

		test_remote_url = 'https://' + self.username + ':' + self.access_token + '@github.com/' + self.username + '/' + self.repository + '.git'
		test_remote_name = 'origin'
		test_url_repo = self.username + '/' + self.repository
		test_url_push = test_url_repo + '/push/' + test_remote_name
		test_url_pull = test_url_repo + '/pull/' + test_remote_name
		test_url_file = test_url_repo + '/file/' + test_file
		test_url_commit = test_url_repo + '/commit'

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Push non-existant repo
		re = self.app.post(test_url_push)
		assert re.status_code == 404 # Not Found

		# Init local repo with remote
		re = self.app.post(test_url_repo, 
			data=json.dumps({test_remote_name: test_remote_url}))
		assert re.status_code == 201 # Created

		# Pull the repo
		re = self.app.post(test_url_pull)
		assert re.status_code == 200 # OK

		# Add new file
		re = self.app.post(test_url_file, 
			data=json.dumps({'data':test_data}))
		assert re.status_code == 201 # Created

		# Commit file
		re = self.app.post(test_url_commit, 
			data=json.dumps({
					'A': [test_file],
					'R': [],
					'msg': 'Unittest ' + time.strftime("%c"),
					'name': 'Unit Test',
					'email': 'UnitTest@gmail.com'
				}))
		assert re.status_code == 200 # OK

		# Push the commit
		re = self.app.post(test_url_push)
		assert re.status_code == 200 # OK

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK

		# Init local repo with remote
		re = self.app.post(test_url_repo, 
			data=json.dumps({test_remote_name: test_remote_url}))
		assert re.status_code == 201 # Created

		# Pull the repo
		re = self.app.post(test_url_pull)
		assert re.status_code == 200 # OK

		# Confirm the contents of the repo
		re = self.app.get(test_url_file)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert j
		assert j['data'] == test_data

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK
		
	def test_file(self):
		test_file = 'test.txt'
		test_data_a = 'Testing 123'
		test_data_b = 'foobar'
		test_url_repo = self.username + '/' + self.repository
		test_url_file = self.username + '/' + self.repository + '/file/' + test_file

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Init local testing repo
		re = self.app.post(test_url_repo, data='{}')
		assert re.status_code == 201 # Created

		# Get non-existant file
		re = self.app.get(test_url_file)
		assert re.status_code == 404

		# Create new file without submitting any data
		re = self.app.post(test_url_file)
		assert re.status_code == 400

		# Create new file
		re = self.app.post(test_url_file, 
			data=json.dumps({'data':test_data_a}))
		assert re.status_code == 201

		# Confirm data stored in file
		re = self.app.get(test_url_file)
		assert re.status_code == 200
		assert json.loads(str(re.data, 'utf-8'))['data'] == test_data_a

		# Update file
		re = self.app.put(test_url_file, 
			data=json.dumps({'data':test_data_b}))
		assert re.status_code == 200

		# Confirm file updated
		re = self.app.get(test_url_file)
		assert re.status_code == 200
		assert json.loads(str(re.data, 'utf-8'))['data'] == test_data_b

		# Delete file
		re = self.app.delete(test_url_file)
		assert re.status_code == 200

		# Confirm deleted
		re = self.app.get(test_url_file)
		assert re.status_code == 404

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK

	def test_list(self):
		test_url_list = '/' + self.username
		test_url_repo = self.username + '/' + self.repository

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Check repo doesn't exist
		re = self.app.get(test_url_list)
		assert re.status_code == 200 or re.status_code == 404
		j = json.loads(str(re.data, 'utf-8'))
		assert self.repository not in j

		# Create repo
		re = self.app.post(test_url_repo, data=json.dumps({}))
		assert re.status_code == 201 # Created

		# Confirm repo exists
		re = self.app.get(test_url_list)
		assert re.status_code == 200
		j = json.loads(str(re.data, 'utf-8'))
		assert self.repository in j

		# Delete repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200

		# Confirm deletion
		re = self.app.get(test_url_list)
		assert re.status_code == 200 or re.status_code == 404
		j = json.loads(str(re.data, 'utf-8'))
		assert self.repository not in j

		
	def test_tree(self):
		test_filename = 'test.txt'
		test_subdir = 'subdir'
		test_data = 'Hello world'
		test_url_repo = self.username + '/' + self.repository
		test_url_tree = test_url_repo + '/tree'
		test_url_file_a = test_url_repo + '/file/' + test_filename
		test_url_file_b = test_url_repo + '/file/' + test_subdir + '/' + test_filename

		# Delete if repo exists from failed tests
		re = self.app.delete(test_url_repo)
		assert re.status_code in [200, 404]

		# Init local testing repo
		re = self.app.post(test_url_repo, data='{}')
		assert re.status_code == 201 # Created

		# Confirm tree is empty
		re = self.app.get(test_url_tree)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert len(j) == 0

		# Create new files
		re = self.app.post(test_url_file_a, data=json.dumps({'data': test_data}))
		assert re.status_code == 201 # Created
		re = self.app.post(test_url_file_b, data=json.dumps({'data': test_data}))
		assert re.status_code == 201 # Created

		# Confirm tree contains new file
		re = self.app.get(test_url_tree)
		assert re.status_code == 200 # OK
		j = json.loads(str(re.data, 'utf-8'))
		assert len(j) == 2
		assert j[test_filename] == True
		assert j[test_subdir][test_filename] == True

		# Delete test repo
		re = self.app.delete(test_url_repo)
		assert re.status_code == 200 # OK


if __name__ == '__main__':
	unittest.main()

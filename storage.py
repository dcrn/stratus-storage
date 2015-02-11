from flask import Flask, request, jsonify
import os, git, shutil

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

@app.route('/<user>/<repo>/file/<path:path>',
		methods=['GET', 'PUT', 'POST', 'DELETE'])
def file(user, repo, path):
	"""
		Provides methods for retrieving, creating, editing and
		deleting files in a repository
		GET: Gets the contents of the file in <path>
			Returns:
					200 (OK) + JSON {data: file contents}
					404 (Not Found)
					500 (Internal Server Error; Can't read file)
		POST: Creates the file at <path> and writes the passed data to it
			Data: JSON with 'data' containing the new file contents
			Returns:
					201 (Created)
					400 (Bad Request; No JSON passed)
					409 (Conflict; File already exists)
					500 (Internal Server Error; Can't write file)
		PUT: Updates the contents of a file
			Data: JSON with 'data' containing the new file contents
			Returns: 
					200 (OK)
					400 (Bad Request; No JSON passed)
					404 (Not Found)
					500 (Internal Server Error; Can't write file)
		DELETE: Deletes a file
			Returns:
					200 (OK)
					404 (Not Found)
					500 (Internal Server Error; Can't delete)
	"""
	root = app.config.get('STORAGE_ROOT')
	fullpath = root + '/' + user + '/' + repo + '/' + path

	exists = os.path.exists(fullpath)
	isdir = os.path.isdir(fullpath)

	if isdir:
		return jsonify({}), 403 # Forbidden

	if request.method == 'GET':
		if exists:
			try:
				with open(fullpath) as f:
					return jsonify({'data': f.read()})
			except Exception as e:
				return jsonify({}), 500 # Internal error
		else:
			return jsonify({}), 404 # Not found

	elif request.method == 'PUT':
		if exists:
			# Confirm json was received
			json = request.get_json(force=True, silent=True)
			if json is None or 'data' not in json:
				return jsonify({}), 400 # Bad request

			# Overwrite file
			try:
				with open(fullpath, 'w') as f:
					f.write(json['data'])
			except Exception as e:
				return jsonify({}), 500 # Internal error

			return jsonify({}), 200 # OK
		else:
			return jsonify({}), 404 # Not Found
	elif request.method == 'POST':
		if exists:
			return jsonify({}), 409 # Conflict

		# Confirm json was received
		json = request.get_json(force=True, silent=True)
		if json is None or 'data' not in json:
			return jsonify({}), 400 # Bad request

		# Make directories if necessary
		os.makedirs(os.path.dirname(fullpath), exist_ok=True)

		# Write data to file
		try:
			with open(fullpath, 'w') as f:
				f.write(json['data'])
		except Exception as e:
			return jsonify({}), 500 # Internal error

		return jsonify({}), 201 # Created

	elif request.method == 'DELETE':
		if exists:
			try:
				os.remove(fullpath)
			except Exception as e:
				return jsonify({}), 500 # Internal error
			return jsonify({}), 200 # OK
		else:
			return jsonify({}), 404 # Not found

	return jsonify({}), 405 # Method not allowed

@app.route('/<user>/<repo>/tree', defaults={'subdir': ''})
@app.route('/<user>/<repo>/tree/<path:subdir>')
def tree(user, repo, subdir):
	"""
		Returns the tree of a directory in JSON, 
			with directories as dictionaries and
			files as 'true'
		GET: Get directory tree
			Returns:
					200 (OK) + JSON
					404 (Not Found; directory does not exist)
	"""
	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	if subdir != '':
		basedir = basedir + '/' + subdir

	if not os.path.exists(basedir):
		return jsonify({}), 404 # Not found

	# Walk the directory and return JSON of tree
	tree = {}
	for path, dir, files in os.walk(basedir):
		localdir = path[len(basedir) + 1:]
		localpath = []

		if localdir != '':
			localpath = localdir.split('/')

		# Ignore .git directory unless specified as the subdirectory
		if '.git' not in localpath:
			wd = tree
			for i in localpath:
				wd[i] = wd.get(i, {})
				wd = wd[i]

			for f in files:
				wd[f] = True

	return jsonify(tree)

@app.route('/<user>/<repo>', 
	methods=['GET', 'PUT', 'POST', 'DELETE'])
def repository(user, repo):
	"""
		Controls the creation and deletion of local git 
			repositories using RESTful methods

		GET: Returns the remotes of a Repository
			Returns: 
					200 (OK) + JSON containing remotes
					404 (Not Found)
		POST: Initializes a new local repository
			Data: JSON object with remote URLs {remote_name: 'remote_url'}
			Returns: 
					201 (Created)
					400 (Bad request, no JSON)
					409 (Conflict; already exists)
		PUT: Updates a repository's remote URLs
			Data: JSON object with remote URLs e.g. {origin: 'https://'}
			Returns: 
					200 (Success)
					400 (Bad request, no JSON)
					404 (Not Found)
		DELETE: Deletes a repository
			Returns: 
					200 (Success)
					404 (Not Found)
	"""

	root = app.config.get('STORAGE_ROOT')
	repodir = root + '/' + user + '/' + repo

	if request.method == 'GET':
		r = None

		# Check if repo exists
		try:
			r = git.Repo(repodir)
		except (git.NoSuchPathError, git.InvalidGitRepositoryError):
			return jsonify({}), 404 # Not Found

		# Return list of remotes
		return jsonify({x.name: x.url for x in r.remotes})
	elif request.method == 'POST':
		# Check if repo already exists
		try:
			git.Repo(repodir)
		except (git.NoSuchPathError, git.InvalidGitRepositoryError):
			pass
		else:
			return jsonify({}), 409 # Conflict

		# Confirm json was received
		json = request.get_json(force=True, silent=True)

		if json is None:
			return jsonify({}), 400 # Bad request

		# Init repo and add remotes
		r = git.Repo.init(repodir)
		for rem in json:
			r.create_remote(rem, json[rem])

		return jsonify({}), 201 # Created

	elif request.method == 'PUT':
		r = None

		# Get repo if it exists
		try:
			r = git.Repo(repodir)
		except (git.NoSuchPathError, git.InvalidGitRepositoryError):
			return jsonify({}), 404 # Not Found

		# Confirm json was received
		json = request.get_json(force=True, silent=True)
		if json is None:
			return jsonify({}), 400 # Bad request

		# Delete existing remotes
		for remo in r.remotes:
			r.delete_remote(remo.name)

		# Replace remotes with passed data
		for rem in json:
			r.create_remote(rem, json[rem])

		return jsonify({}), 200 # OK

	elif request.method == 'DELETE':
		r = None

		# Check if repo exists
		try:
			r = git.Repo(repodir)
		except (git.NoSuchPathError, git.InvalidGitRepositoryError):
			return jsonify({}), 404 # Not Found

		try:
			shutil.rmtree(repodir)
		except:
			return jsonify({}), 500 # Interal server error

		return jsonify({}), 200


	return jsonify({}), 405 # Method not allowed

@app.route('/<user>/<repo>/status')
def status(user, repo):
	"""
		Gets the git status of a repository, including the diff 
		between the last commit and the working dirctory.

		GET: Get repo status
			Returns: 
				200 (OK) + JSON object consisting of modified filenames 
					grouped by Addition (A), Modification (M), 
					Deletion (D), Rename (R) and Untracked (U).
				403 (Forbidden) No baseline commit to diff with
				404 (Not Found)
	"""

	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	r = None
	try:
		r = git.Repo(basedir)
	except (git.NoSuchPathError, git.InvalidGitRepositoryError):
		return jsonify({}), 404 # Not Found

	if not r.head.is_valid():
		return jsonify({}), 403 # Forbidden

	# Get the diff of the last commit and the working directory
	diffs = r.head.commit.diff(None)

	# Iterate diffs and add them to a dictionary grouped by change type (Add, Modify, Delete, Rename, Untracked)
	changes = {}
	for ct in diffs.change_type:
		changes[ct] = []
		for diff in diffs.iter_change_type(ct):
			c = {}
			if diff.a_blob:
				c['A'] = diff.a_blob.path
			if diff.b_blob:
				c['B'] = diff.b_blob.path
			changes[ct].append(c)

	changes['U'] = r.untracked_files

	return jsonify(changes)

@app.route('/<user>/<repo>/push/<remote>/<branch>', methods=['GET'])
def push(user, repo, remote, branch):
	"""
		Performs a git push to the specified remote branch
		GET: Push the local changes to the remote server
			Returns:
				200 (OK)
				403 (Forbidden; remote doesn't exist)
				404 (Not Found)
	"""
	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	r = None
	try:
		r = git.Repo(basedir)
	except (git.NoSuchPathError, git.InvalidGitRepositoryError):
		return jsonify({}), 404 # Not Found

	return ''

@app.route('/<user>/<repo>/pull/<remote>/<branch>', methods=['GET'])
def pull(user, repo, remote, branch):
	"""
		Performs a git pull from remote branch
		GET: Pull the remote changes to the local repo
			Returns:
				200 (OK)
				403 (Forbidden; remote doesn't exist)
				404 (Not Found)
	"""
	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	r = None
	try:
		r = git.Repo(basedir)
	except (git.NoSuchPathError, git.InvalidGitRepositoryError):
		return jsonify({}), 404 # Not Found

	return ''

@app.route('/<user>/<repo>/commit', methods=['POST'])
def commit(user, repo):
	"""
		Commits changes locally based on JSON submitted 
			which contains a list of files and a message
			to be commited
		POST: Perform the commit
			Data:
				JSON object containing a list of files to
					(A)dd or (R)emove and a commit message (msg).
					e.g. {
							'A': ['dir/hello.txt']
							'R': ['foo.txt']
							'msg': 'Added hello, removed foo'
						}
			Returns:
				200 (OK)
				400 (Bad Request; invalid or no JSON)
				404 (Not Found)
	"""
	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	r = None
	try:
		r = git.Repo(basedir)
	except (git.NoSuchPathError, git.InvalidGitRepositoryError):
		return jsonify({}), 404 # Not Found

	return ''

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
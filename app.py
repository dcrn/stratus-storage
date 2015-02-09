from flask import Flask, request, jsonify
import os, git, shutil

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

@app.route('/<user>/<repo>/file/<path:path>',
		methods=['GET', 'PUT', 'DELETE'])
def file(user, repo, path):
	root = app.config.get('STORAGE_ROOT')
	fullpath = root + '/' + user + '/' + repo + '/' + path

	exists = os.path.exists(fullpath)
	isdir = os.path.isdir(fullpath)

	if isdir:
		return jsonify({}), 403 # Forbidden

	if request.method == 'GET':
		if exists:
			with open(fullpath) as f:
				return jsonify({'data': f.read()})
		else:
			return jsonify({}), 404 # Not found

	elif request.method == 'PUT':
		if exists:
			with open(fullpath, 'w') as f:
				f.write(request.data)
			return jsonify({}), 202 # Accepted
		else:
			# Make directories if necessary
			os.makedirs(os.path.dirname(fullpath), exist_ok=True)

			with open(fullpath, 'w') as f:
				f.write(request.data)
			return jsonify({}), 201 # Created

	elif request.method == 'DELETE':
		if exists:
			os.remove(fullpath)
			return jsonify({}), 202 # Accepted
		else:
			return jsonify({}), 404 # Not found

	return jsonify({}), 500 # Internal error

@app.route('/<user>/<repo>/tree', defaults={'subdir': ''})
@app.route('/<user>/<repo>/tree/<path:subdir>')
def tree(user, repo, subdir):
	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	if subdir != '':
		basedir = basedir + '/' + subdir

	if not os.path.exists(basedir):
		return jsonify({}), 404

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

# Git operations
@app.route('/<user>/<repo>/status')
def status(user, repo):
	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo
	r = git.Repo(basedir)

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

@app.route('/<user>/<repo>/push')
def push(user, repo):
	access_token = request.args.get('access_token')
	if access_token == None:
		return jsonify({}), 403 # Forbidden

	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo
	r = git.Repo(basedir)
	return ''

@app.route('/<user>/<repo>/pull')
def pull(user, repo):
	access_token = request.args.get('access_token')
	if access_token == None:
		return jsonify({}), 403 # Forbidden

	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo
	r = git.Repo(basedir)
	return ''

@app.route('/<user>/<repo>/commit')
def commit(user, repo):
	access_token = request.args.get('access_token')
	if access_token == None:
		return jsonify({}), 403 # Forbidden

	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo
	r = git.Repo(basedir)
	return ''

@app.route('/<user>/<repo>/clone')
def clone(user, repo):
	access_token = request.args.get('access_token')
	if access_token == None:
		return jsonify({}), 403 # Forbidden

	root = app.config.get('STORAGE_ROOT')
	basedir = root + '/' + user + '/' + repo

	# Remove any existing data
	shutil.rmtree(basedir, ignore_errors=True)

	# Make the repo
	os.makedirs(basedir, exist_ok=True)
	r = git.Repo.init(basedir, mkdir=False)

	# Add remote with authentication
	rem = r.create_remote('origin', 'https://' + user + ':' + access_token + '@github.com/' + user + '/' + repo + '.git')

	# Pull existing data from GitHub
	rem.fetch()
	rem.pull(rem.refs[0].remote_head)

	return ''

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)
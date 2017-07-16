#!/bin/env python3
#
# Update the local git repo and rebuild the parts database

import git
import json
import os
import sys
import glob

from dbmodel import *

class GitProgress(git.remote.RemoteProgress):
	def update(self, op_code, cur_count, max_count=None, message=''):
		#print('update(%s, %s, %s, %s)'%(op_code, cur_count, max_count, message))
		sys.stdout.write("\r" + self._cur_line)
		if (op_code & git.remote.RemoteProgress.END != 0):
			sys.stdout.write("\n")

def setup_repo(repodir, conf):
	url = conf.get("origin", "http://github.com/eldstal/replacement-parts")
	branch = conf.get("branch", "master")


	g = os.path.join(repodir, ".git")
	if (not os.path.isdir(g)):
		os.mkdir(repodir)
		git.Repo.clone_from(url, repodir, progress=GitProgress())

	repo = git.Repo(repodir)
	repo.remote().pull(progress=GitProgress())
	repo.git.checkout(branch)
	return repo

def main():

	# This way, relative paths in the configuration file also work painlessly
	basedir = os.path.dirname(__file__)
	os.chdir(basedir)

	configfile = "config.json"

	with open(configfile) as f:
		conf = json.load(f)

	repodir = conf.get("storage", "parts-repo")
	dbfile = conf.get("database", "database.sqlite")

	# Fetch up-to-date files
	repo = setup_repo(repodir, conf)

	# Connect to the SQL database
	db = setup_database()

	# Find all metadata files and load them into the database
	mdfiles = glob.glob(os.path.join(repodir, "*", "*", "*", "metadata.json"))
	for mdf in mdfiles:
		with open(mdf) as f:
			try:
				p, _ = os.path.split(mdf)
				p, part = os.path.split(p)
				p, dev = os.path.split(p)
				p, sys = os.path.split(p)
				path = "/".join([sys, dev, part])

				metadata = json.load(f)
				author = metadata["author"]
				part_class = metadata["class"]
				fits = sorted(list(set(metadata["fits"])))
				license = metadata["license"]
				description = metadata["description"]
			except e:
				sys.stderr.write("Unable to load part %s: %s\n", (path, e))
				continue

			#
			# Part entry in the database
			#
			values = {
			          "system": sys,
			          "device": dev,
			          "part": part,
			          "author": author,
			          "part_class": part_class,
			          "fits": fits,
			          "license": license,
			          "description": description
			         }

			# If this part (matched by name) already exists,
			# update it to maintain the old uuid
			existing = Part.select().where((Part.system == sys) &
			                               (Part.device == dev) &
				                             (Part.part == part)
																)
			if (len(existing) > 0):
				# Reuse existing UUID
				desc = existing.get()
				query = Part.update(**values).where(Part.uuid == desc.uuid)
				query.execute()
			else:
				# Automatically assigned a new UUID
				desc = Part.create(uuid=new_uuid(), **values)
				print("Created with UUID %s" % desc.uuid)
				Counter.create(uuid=desc.uuid)
				desc.save()

			print(path)


			#
			# Generate a screenshot
			#


			#
			# Archive the source files for this part, if they have changed
			#



	db.close()


if __name__ == '__main__':
		sys.exit(main())

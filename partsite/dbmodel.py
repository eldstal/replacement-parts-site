from peewee import *
import uuid
import json
import sys

# Peewee is written with static and global database in mind. WTF?
DATABASE = SqliteDatabase("parts-site.sqlite")

class BaseModel(Model):
	class Meta:
		database = DATABASE

class ListField(Field):
	db_field='varchar'
	def db_value(self, value):
		return json.dumps(value)				# FIXME: Not quite safe
	def python_value(self, value):
		return json.loads(value)					# FIXME: Not quite safe

class Version(BaseModel):
	version = IntegerField()

class Part(BaseModel):
	# Unique primary key, randomly generated
	uuid = TextField(primary_key=True)

	# Portions of the path
	system = TextField()
	device = TextField()
	part = TextField()

	# Metadata from the metadata.json file
	author = TextField()
	part_class = TextField()
	fits = ListField()				# List of strings
	license = TextField()
	description = TextField()

class Counter(BaseModel):
	uuid = ForeignKeyField(Part)
	views = IntegerField(default=0)
	downloads = IntegerField(default=0)


def new_uuid():
	# XXX: Try again if it happens to be taken
	return uuid.uuid4()

def setup_database():
	DATABASE.connect()

	# If there is nothing at all in the database,
	# create the tables
	try:
		v = Version.get()
		sys.stderr.write("Database v%d opened\n" % v.version)
	except:
		sys.stderr.write("Creating new database\n");
		DATABASE.create_tables([Version, Part, Counter])
		Version.create(version=1).save()

	# TODO: database upgrade here

	return DATABASE

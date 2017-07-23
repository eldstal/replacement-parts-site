#!/bin/env python3

from flask import Flask
from flask import render_template, url_for

from itertools import chain

from partsite.dbmodel import *



app = Flask(__name__)

database = DATABASE

def all_systems():
	return [ p.system for p in Part.select(Part.system).distinct() ]

# Used to generate the menus
# Two lists, one of systems and one of devices.
# Each list entry is a tuple of (title, url)
def nav_pages(sys=None, dev=None):
	systems = []
	devices = []
	models = []

	systems += [ (s, url_for("system", sys=s))  for s in all_systems() ]

	if (sys is not None):
		devices = [ (p.device, url_for("device", sys=sys, dev=p.device)) for p in Part.select(Part.device).distinct().where(Part.system == sys) ]

	if (dev is not None):
		# All (unique) model numbers known for this device.
		models = [ p.fits for p in Part.select(Part.fits).where((Part.system == sys) & (Part.device == dev)) ]
		models = sorted(list(set(chain.from_iterable(models))))

	return (systems, devices, models)


# Functions exposed to jinja
@app.context_processor
def export_funcs():
	return dict(nav_pages=nav_pages)

@app.before_request
def before_request():
	database.connect()

@app.after_request
def after_request(response):
	database.close()
	return response

@app.teardown_appcontext
def close_db(error):
	database.close()

@app.errorhandler(404)
def error_404(error):
	return render_template("404.html", message=error), 404

@app.route('/')
def index():
	return render_template("index.html", system="index")


@app.route('/system/<sys>/')
def system(sys):
	systems = all_systems()

	# Handle unknown systems
	if (sys not in systems):
		return error_404("System %s unknown" % sys)

	# List all parts for this system
	parms = {
					"system": sys,
					"parts": Part.select().where((Part.system == sys))
					}

	return render_template("listing.html", **parms)


# Display the information for a device (for example, /nes/controller/)
@app.route('/device/<sys>/<dev>')
def device(sys, dev):
	systems = all_systems()

	# Handle unknown systems
	if (sys not in systems):
		return error_404("System %s unknown" % sys)

	# List all parts for this system
	parms = {
					"system": sys,
					"device": dev,
					"parts": Part.select().where((Part.system == sys) & (Part.device == dev))
					}

	return render_template("listing.html", **parms)


# Display the information for a model number, for example /nes/nese-430
@app.route('/model/<sys>/<mdl>')
def model(sys, mdl):
	systems = all_systems()

	# Handle unknown systems
	if (sys not in systems):
		return error_404("System %s unknown" % sys)

	# List all parts that fit the selected model
	all_parts = Part.select().where((Part.system == sys)).order_by(Part.device, Part.part)
	fitting_parts = [ p for p in all_parts if mdl in p.fits ]

	# List all parts for this system
	parms = {
					"system": sys,
					"model": mdl,
					"parts": fitting_parts
					}

	return render_template("listing.html", **parms)

# Display the information for a part (for example, /nes/controller/a.button)
@app.route('/part/<sys>/<dev>/<prt>')
def part(sys, dev, prt):

	matches = Part.select().where((Part.system == sys) & (Part.device == dev) & (Part.part == prt))

	if (len(matches) == 0):
		return error_404("Part not found")

	info = matches.get()

	# List all parts for this system
	parms = {
					"system": sys,
					"device": dev,
					"part": prt,
					"info": info
					}

	return render_template("part.html", **parms)



# Disable all browser caching
@app.after_request
def add_header(r):
	"""
	Add headers to both force latest IE rendering engine or Chrome Frame,
	and also to cache the rendered page for 10 minutes.
	"""
	r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	r.headers["Pragma"] = "no-cache"
	r.headers["Expires"] = "0"
	r.headers['Cache-Control'] = 'public, max-age=0'
	return r

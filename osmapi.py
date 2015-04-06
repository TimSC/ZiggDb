#Recipe for apache: http://webpy.org/cookbook/mod_wsgi-apache
#Jinja2 templating using solution 2 from: http://webpy.org/cookbook/template_jinja

#sudo apt-get install apache2 libapache2-mod-wsgi python-dev python-jinja2

import web, os, sys, datetime, json, math
sys.path.append(os.path.dirname(__file__))
import StringIO
import config, zigg
from jinja2 import Environment, FileSystemLoader
from xml.sax.saxutils import escape

class ApiMap(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def Render(self):
		webInput = web.input()
		ziggDb = web.ctx.ziggDb
		idCount = {"node": 1, "way": 1, "relation": 1}

		bbox = map(float, webInput["bbox"].split(","))
		area = ziggDb.GetArea(bbox)

		out = [u"<?xml version='1.0' encoding='UTF-8'?>\n"]
		out.append(u"<osm version='0.6' upload='true' generator='ZiggDb'>\n")
  		out.append(u"<bounds minlat='{0}' minlon='{1}' maxlat='{2}' maxlon='{3}' origin='ZiggDb' />".format(
			bbox[1], bbox[0], bbox[3], bbox[2]))

		for nodeId in area["nodes"]:
			objShapes, objData = area["nodes"][nodeId]
			shape = objShapes[0]
			outer, inners = shape
			pt = outer[0]

			out.append(u"<node id='{0}' timestamp='2006-11-30T00:03:33Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' lat='{1}' lon='{2}'>\n".format(idCount["node"], pt[0], pt[1]))
			idCount["node"] += 1
			for key in objData:
				out.append(u"  <tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
			out.append(u"</node>\n")

		out.append(u"</osm>\n")

		web.header('Content-Type', 'text/xml')
		return "".join(out).encode("utf-8")

urls = (
	'/api/0.6/map', 'ApiMap',
	)

def RenderTemplate(template_name, **context):
	extensions = context.pop('extensions', [])
	globals = context.pop('globals', {})

	jinja_env = Environment(
			loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
			extensions=extensions,
			)
	jinja_env.globals.update(globals)
	jinja_env.filters['datetime'] = Jinja2DateTime

	#jinja_env.update_template_context(context)
	return jinja_env.get_template(template_name).render(context)

def InitDatabaseConn():
	curdir = os.path.dirname(__file__)
	#web.ctx.dataDb = web.database(dbn='sqlite', db=os.path.join(curdir, 'data.db'))
	#web.ctx.users = web.database(dbn='sqlite', db=os.path.join(curdir, 'users.db'))
	web.ctx.ziggDb = zigg.ZiggDb(config.repos, os.path.dirname(__file__))
	web.ctx.session = session

web.config.debug = 1
app = web.application(urls, globals())
curdir = os.path.dirname(__file__)
app.add_processor(web.loadhook(InitDatabaseConn))

session = web.session.Session(app, web.session.DiskStore(os.path.join(curdir,'sessions')),)

application = app.wsgifunc()



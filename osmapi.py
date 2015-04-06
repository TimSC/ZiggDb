#Recipe for apache: http://webpy.org/cookbook/mod_wsgi-apache
#Jinja2 templating using solution 2 from: http://webpy.org/cookbook/template_jinja

#sudo apt-get install apache2 libapache2-mod-wsgi python-dev python-jinja2

import web, os, sys, datetime, json, math
from sqlitedict import SqliteDict
sys.path.append(os.path.dirname(__file__))
import StringIO
import config, zigg
from jinja2 import Environment, FileSystemLoader
from xml.sax.saxutils import escape

class ApiMap(object):
	def GET(self):
		#Add a global lock TODO
		return self.Render()

	def POST(self):
		#Add a global lock TODO
		return self.Render()

	def AssignId(self, objType, uuid, subObject = None):
		lastIdsDb = web.ctx.lastIdsDb
		nodeIdToUuidDb = web.ctx.nodeIdToUuidDb
		uuidToNodeIdDb = web.ctx.uuidToNodeIdDb

		wayIdToUuidDb = web.ctx.wayIdToUuidDb
		uuidToWayIdDb = web.ctx.uuidToWayIdDb

		relationIdToUuidDb = web.ctx.relationIdToUuidDb
		uuidToRelationIdDb = web.ctx.uuidToRelationIdDb

		cid = uuid
		if subObject is not None:
			cid += subObject

		#Check if ID already assigned
		if objType == "node" and cid in uuidToNodeIdDb:
			return int(uuidToNodeIdDb[str(cid)])

		if objType == "way" and cid in uuidToWayIdDb:
			return int(uuidToWayIdDb[str(cid)])

		if objType == "relation" and cid in uuidToRelationIdDb:
			return int(uuidToRelationIdDb[str(cid)])

		#Assign a new ID
		newId = None
		if objType in lastIdsDb:
			newId = int(lastIdsDb[objType]) + 1
		else:
			newId = 1

		lastIdsDb[objType] = str(newId)

		if objType == "node":
			nodeIdToUuidDb[str(newId)] = str(cid)
			uuidToNodeIdDb[str(cid)] = str(newId)

		if objType == "way":
			wayIdToUuidDb[str(newId)] = str(cid)
			uuidToWayIdDb[str(cid)] = str(newId)

		if objType == "relation":
			relationIdToUuidDb[str(newId)] = str(cid)
			uuidToRelationIdDb[str(cid)] = str(newId)

		return newId

	def Render(self):
		webInput = web.input()
		ziggDb = web.ctx.ziggDb

		bbox = map(float, webInput["bbox"].split(","))
		area = ziggDb.GetArea(bbox)
		nodesWritten = set()

		out = [u"<?xml version='1.0' encoding='UTF-8'?>\n"]
		out.append(u"<osm version='0.6' upload='true' generator='ZiggDb'>\n")
  		out.append(u"<bounds minlat='{0}' minlon='{1}' maxlat='{2}' maxlon='{3}' origin='ZiggDb' />".format(
			bbox[1], bbox[0], bbox[3], bbox[2]))

		#Write individual nodes to output
		for nodeId in area["nodes"]:
			objShapes, objData = area["nodes"][nodeId]
			shape = objShapes[0]
			outer, inners = shape
			pt = outer[0]
			nid = self.AssignId("node", nodeId)

			out.append(u"<node id='{0}' timestamp='2006-11-30T00:03:33Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' lat='{1}' lon='{2}'>\n".format(nid, pt[0], pt[1]))
			for key in objData:
				out.append(u"  <tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
			out.append(u"</node>\n")

			nodesWritten.add(nodeId)

		#Write nodes that are part of other objects
		for objType in ["ways", "areas"]:
			objDict = area[objType]
			for objId in objDict:
				objShapes, objData = objDict[objId]
				shape = objShapes[0]
				outer, inners = shape
				for pt in outer:
					if pt[2] in nodesWritten: continue #Already written to output

					nid = self.AssignId("node", pt[2])

					out.append(u"<node id='{0}' timestamp='2006-11-30T00:03:33Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' lat='{1}' lon='{2}'>\n".format(nid, pt[0], pt[1]))

					out.append(u"</node>\n")

					nodesWritten.add(pt[2])

				if inners is None: continue
				for inner in inners:
					for pt in inner:
						if pt[2] in nodesWritten: continue #Already written to output

						nid = self.AssignId("node", pt[2])
						out.append(u"<node id='{0}' timestamp='2006-11-30T00:03:33Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' lat='{1}' lon='{2}'>\n".format(nid, pt[0], pt[1]))
						out.append(u"</node>\n")

						nodesWritten.add(pt[2])

		#Write ways
		for objType in ["ways"]:
			objDict = area[objType]
			for objId in objDict:
				objShapes, objData = objDict[objId]
				shape = objShapes[0]
				outer, inners = shape
				oid = self.AssignId("way", objId, "o")

				out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
				for pt in outer:
					nid = self.AssignId("node", pt[2])
					out.append(u"<nd ref='{0}' />\n".format(nid))
				for key in objData:
					out.append(u"<tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
				out.append(u"</way>\n")

		areaIdMap = {}
		areaUuidMap = {}

		#Write way for areas if no inner ways are present
		for objType in ["areas"]:
			objDict = area[objType]
			for objId in objDict:
				objShapes, objData = objDict[objId]
				shape = objShapes[0]
				outer, inners = shape
				if len(inners) != 0: continue

				#Write outer way
				oid = self.AssignId("way", objId)
				out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
				for pt in outer:
					nid = self.AssignId("node", pt[2])
					out.append(u"<nd ref='{0}' />\n".format(nid))
				nid = self.AssignId("node", outer[0][2]) #Close area
				out.append(u"<nd ref='{0}' />\n".format(nid))
				out.append(u"  <tag k='area' v='yes' />\n")
				for key in objData:
					out.append(u"  <tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
				out.append(u"</way>\n")

		#Write ways for areas if inner ways are present
		for objType in ["areas"]:
			objDict = area[objType]
			for objId in objDict:
				objShapes, objData = objDict[objId]
				shape = objShapes[0]
				outer, inners = shape
				if len(inners) == 0: continue

				#Write outer way
				oid = self.AssignId("way", objId, "o")
				out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
				wayOuterId = oid
				for pt in outer:
					nid = self.AssignId("node", pt[2])
					out.append(u"<nd ref='{0}' />\n".format(nid))
				nid = self.AssignId("node", outer[0][2]) #Close area
				out.append(u"<nd ref='{0}' />\n".format(nid))
				out.append(u"</way>\n")

				#Writer inner ways
				wayInnersIds = []
				if inners is not None:
					for i, inner in enumerate(inners):
						oid = self.AssignId("way", objId, "i{0}".format(i))
						out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' inner='1'>\n".format(oid))
						wayInnersIds.append(oid)
						for pt in inner:
							nid = self.AssignId("node", pt[2])
							out.append(u"<nd ref='{0}' />\n".format(nid))
						nid = self.AssignId("node", inner[0][2]) #Close area
						out.append(u"<nd ref='{0}' />\n".format(nid))
						out.append(u"</way>\n")			
				
				areaUuidMap[objId] = (wayOuterId, wayInnersIds)
		
		#Tie together multipolygons with relations
		for objType in ["areas"]:
			objDict = area[objType]
			for objId in objDict:
				objShapes, objData = objDict[objId]
				shape = objShapes[0]
				outer, inners = shape
				if len(inners) == 0: continue
				wayOuterId, wayInnerIds = areaUuidMap[objId]

				oid = self.AssignId("relation", objId)
				out.append(u"<relation id='{0}' timestamp='2008-03-10T17:43:07Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(
					oid))
				out.append(u"  <member type='way' ref='{0}' role='outer' />\n".format(wayOuterId))
				for wid in wayInnerIds:
					out.append(u"  <member type='way' ref='{0}' role='inner' />\n".format(wid))
				out.append(u"  <tag k='type' v='multipolygon' />\n")
				for key in objData:
					out.append(u"  <tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
				out.append(u"</relation>\n")


		out.append(u"</osm>\n")

		web.header('Content-Type', 'text/xml')
		return "".join(out).encode("utf-8")

class ApiBase(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def Render(self):
		web.header('Content-Type', 'text/plain')
		return "Base url for API"

class ApiCapabilities(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def Render(self):
		web.header('Content-Type', 'text/xml')
		out = []

		out.append(u'<?xml version="1.0" encoding="UTF-8"?>')
		out.append(u'<osm version="0.6" generator="ZiggDb" copyright="TBD" attribution="TBD" license="TBD">')
		out.append(u'  <api>')
		out.append(u'    <version minimum="0.6" maximum="0.6"/>')
		out.append(u'    <area maximum="0.25"/>')
		out.append(u'    <tracepoints per_page="5000"/>')
		out.append(u'    <waynodes maximum="2000"/>')
		out.append(u'    <changesets maximum_elements="50000"/>')
		out.append(u'    <timeout seconds="300"/>')
		out.append(u'    <status database="online" api="online" gpx="online"/>')
		out.append(u'  </api>')
		out.append(u'  <policy>')
		out.append(u'    <imagery>')
		out.append(u'      <blacklist regex=".*\.googleapis\.com/.*"/>')
		out.append(u'      <blacklist regex=".*\.google\.com/.*"/>')
		out.append(u'      <blacklist regex=".*\.google\.ru/.*"/>')
		out.append(u'    </imagery>')
		out.append(u'  </policy>')
		out.append(u'</osm>')

		return "".join(out).encode("utf-8")

urls = (
	'/api/0.6/map', 'ApiMap',
	'/api/capabilities', 'ApiCapabilities',
	'/api/0.6/capabilities', 'ApiCapabilities',
	'/', 'ApiBase'
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
	
	web.ctx.nodeIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'nodeIdToUuidDb.sqlite'), autocommit=True)
	web.ctx.uuidToNodeIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToNodeIdDb.sqlite'), autocommit=True)

	web.ctx.wayIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'wayIdToUuidDb.sqlite'), autocommit=True)
	web.ctx.uuidToWayIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToWayIdDb.sqlite'), autocommit=True)

	web.ctx.relationIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'relationIdToUuidDb.sqlite'), autocommit=True)
	web.ctx.uuidToRelationIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToRelationIdDb.sqlite'), autocommit=True)

	web.ctx.lastIdsDb = SqliteDict(os.path.join(curdir, 'data', 'lastIdsDb.sqlite'), autocommit=True)
	web.ctx.ziggDb = zigg.ZiggDb(config.repos, curdir)
	#web.ctx.session = session

web.config.debug = 1
app = web.application(urls, globals())
curdir = os.path.dirname(__file__)
app.add_processor(web.loadhook(InitDatabaseConn))

#session = web.session.Session(app, web.session.DiskStore(os.path.join(curdir,'sessions')),)

application = app.wsgifunc()



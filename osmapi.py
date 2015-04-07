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
import xml.etree.ElementTree as ET

class IdAssignment(object):
	def __init__(self):
		pass

	def AssignId(self, objType, uuid = None, subObject = None):
		lastIdsDb = web.ctx.lastIdsDb
		nodeIdToUuidDb = web.ctx.nodeIdToUuidDb
		uuidToNodeIdDb = web.ctx.uuidToNodeIdDb

		wayIdToUuidDb = web.ctx.wayIdToUuidDb
		uuidToWayIdDb = web.ctx.uuidToWayIdDb

		relationIdToUuidDb = web.ctx.relationIdToUuidDb
		uuidToRelationIdDb = web.ctx.uuidToRelationIdDb

		cid = ""
		if uuid is not None:
			cid += uuid
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


class ApiMap(object):
	def GET(self):
		#Add a global lock TODO
		return self.Render()

	def POST(self):
		#Add a global lock TODO
		return self.Render()


	def Render(self):
		webInput = web.input()
		ziggDb = web.ctx.ziggDb
		idAssignment = IdAssignment()

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
			nid = idAssignment.AssignId("node", nodeId)

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

					nid = idAssignment.AssignId("node", pt[2])

					out.append(u"<node id='{0}' timestamp='2006-11-30T00:03:33Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' lat='{1}' lon='{2}'>\n".format(nid, pt[0], pt[1]))

					out.append(u"</node>\n")

					nodesWritten.add(pt[2])

				if inners is None: continue
				for inner in inners:
					for pt in inner:
						if pt[2] in nodesWritten: continue #Already written to output

						nid = idAssignment.AssignId("node", pt[2])
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
				oid = idAssignment.AssignId("way", objId, "o")

				out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
				for pt in outer:
					nid = idAssignment.AssignId("node", pt[2])
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
				oid = idAssignment.AssignId("way", objId)
				out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
				for pt in outer:
					nid = idAssignment.AssignId("node", pt[2])
					out.append(u"<nd ref='{0}' />\n".format(nid))
				nid = idAssignment.AssignId("node", outer[0][2]) #Close area
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
				oid = idAssignment.AssignId("way", objId, "o")
				out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
				wayOuterId = oid
				for pt in outer:
					nid = idAssignment.AssignId("node", pt[2])
					out.append(u"<nd ref='{0}' />\n".format(nid))
				nid = idAssignment.AssignId("node", outer[0][2]) #Close area
				out.append(u"<nd ref='{0}' />\n".format(nid))
				out.append(u"</way>\n")

				#Writer inner ways
				wayInnersIds = []
				if inners is not None:
					for i, inner in enumerate(inners):
						oid = idAssignment.AssignId("way", objId, "i{0}".format(i))
						out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' inner='1'>\n".format(oid))
						wayInnersIds.append(oid)
						for pt in inner:
							nid = idAssignment.AssignId("node", pt[2])
							out.append(u"<nd ref='{0}' />\n".format(nid))
						nid = idAssignment.AssignId("node", inner[0][2]) #Close area
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

				oid = idAssignment.AssignId("relation", objId)
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

		web.header('Content-Type', 'text/xml')
		return "".join(out).encode("utf-8")

class ApiChangesetCreate(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def PUT(self):
		return self.Render()

	def Render(self):
		idAssignment = IdAssignment()
		cid = idAssignment.AssignId("changeset")
		webInput = web.input()
		webData = web.data()


		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "{0}.txt".format(requestNum)), "wt")
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput)+"\n")
		fi.write(str(web.ctx.env.copy())+"\n")
		fi.write(str(web.data())+"\n")
		fi.write("response\n")
		fi.write(str(cid)+"\n")

		fi.close()

		web.header('Content-Type', 'text/plain')
		return str(cid).encode("utf-8")

class ApiChangesets(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def PUT(self):
		return self.Render()

	def Render(self):
		idAssignment = IdAssignment()
		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "{0}.txt".format(requestNum)), "wt")
		webInput = web.input()
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput))
		fi.close()

		return "bonk"

class ApiChangeset(object):
	def GET(self, cid):

		out = []
		out.append(u'<?xml version="1.0" encoding="UTF-8"?>')
		out.append(u'<osm version="0.6" generator="ZiggDb" copyright="TBD" attribution="TBD" license="TBD">\n')
		out.append(u'<changeset id="{0}" user="ZiggDb" uid="1" created_at="2006-01-26T01:23:30Z" closed_at="2006-01-26T03:19:55Z" open="false" min_lat="58.4069356" min_lon="15.5864985" max_lat="58.4188714" max_lon="15.6195092" comments_count="0"/>\n'.format(cid))
		out.append(u'</osm>\n')
		
		web.header('Content-Type', 'text/xml')
		return "".join(out).encode("utf-8")

	def POST(self, cid):
		return self.Render(cid)

	def PUT(self, cid):
		return self.Render(cid)

	def Render(self, cid):
		idAssignment = IdAssignment()

		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "{0}.txt".format(requestNum)), "wt")
		webData = web.data()
		webInput = web.input()
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput)+"\n")
		fi.write(str(cid)+"\n")
		fi.write(str(web.ctx.env.copy())+"\n")
		fi.write(str(web.data())+"\n")
		fi.close()

		web.header('Content-Type', 'text/xml')
		return "bonk"

class ApiChangesetUpload(object):

	def POST(self, cid):
		return self.Render(cid)

	def Render(self, cid):
		idAssignment = IdAssignment()
		webData = web.data()
		nodeCount = 100

		newNodes = []
		root = ET.fromstring(webData)
		for meth in root:
			method = meth.tag
			for el in meth:
				objTy = el.tag
				objId = int(el.attrib["id"])
				objCid = int(el.attrib["changeset"])
				if objTy == "node":
					objLat = float(el.attrib["lat"])
					objLon = float(el.attrib["lon"])

					newId = nodeCount
					nodeCount += 1

					newNodes.append((objId, newId))

		out = []
		out.append(u'<?xml version="1.0" encoding="UTF-8"?>\n')
		out.append(u'<diffResult generator="OpenStreetMap Server" version="0.6">\n')
		for nd in newNodes:
			out.append(u'<node old_id="{0}" new_id="{1}" new_version="{2}"/>\n'.format(nd[0], nd[1], 1))
		out.append(u'</diffResult>\n')

		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "{0}.txt".format(requestNum)), "wt")
		webInput = web.input()
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput)+"\n")
		fi.write(str(cid)+"\n")
		fi.write(str(web.ctx.env.copy())+"\n")
		fi.write(str(web.data())+"\n")
		fi.write("response:\n")
		fi.write("".join(out).encode("utf-8")+"\n")
		fi.close()

		web.header('Content-Type', 'text/xml')
		return u"".join(out).encode("utf-8")

class ApiChangesetClose(object):
	def GET(self, cid):
		return self.Render(cid)

	def POST(self, cid):
		return self.Render(cid)

	def PUT(self, cid):
		return self.Render(cid)

	def Render(self, cid):
		idAssignment = IdAssignment()

		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "{0}.txt".format(requestNum)), "wt")
		webData = web.data()
		webInput = web.input()
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput)+"\n")
		fi.write(str(cid)+"\n")
		fi.write(str(web.ctx.env.copy())+"\n")
		fi.write(str(web.data())+"\n")
		fi.close()

		web.header('Content-Type', 'text/plain')
		return "" #Nothing is returned

class ApiUserDetails(object):
	def GET(self):
		return self.Render()

	def POST(self):
		return self.Render()

	def PUT(self):
		return self.Render()

	def Render(self):

		out = []
		out.append(u'<?xml version="1.0" encoding="UTF-8"?>\n')
		out.append(u'<osm version="0.6" generator="ZiggDb">\n')
		out.append(u'  <user id="1" display_name="ApiTests" account_created="2013-07-21T17:53:45Z">\n')
		out.append(u'    <description></description>\n')
		#out.append(u'    <img href=""/>\n')
		out.append(u'    <roles>\n')
		out.append(u'    </roles>\n')
		out.append(u'    <changesets count="1"/>\n')
		out.append(u'    <traces count="0"/>\n')
		out.append(u'    <blocks>\n')
		out.append(u'      <received count="0" active="0"/>\n')
		out.append(u'    </blocks>\n')
		out.append(u'    <languages>\n')
		out.append(u'      <lang>en-GB</lang>\n')
		out.append(u'      <lang>en</lang>\n')
		out.append(u'    </languages>\n')
		out.append(u'    <messages>\n')
		out.append(u'      <received count="0" unread="0"/>\n')
		out.append(u'      <sent count="0"/>\n')
		out.append(u'    </messages>\n')
		out.append(u'  </user>\n')
		out.append(u'</osm>\n')

		idAssignment = IdAssignment()
		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "{0}.txt".format(requestNum)), "wt")
		webInput = web.input()
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput))
		fi.close()

		web.header('Content-Type', 'text/xml')
		return u"".join(out).encode("utf-8")

urls = (
	'/api/0.6/map', 'ApiMap',
	'/api/capabilities', 'ApiCapabilities',
	'/api/0.6/capabilities', 'ApiCapabilities',
	'/api/0.6/changeset/create', 'ApiChangesetCreate',
	'/api/0.6/user/details', 'ApiUserDetails',
	'/api/0.6/changesets', 'ApiChangesets',
	'/api/0.6/changeset/([0-9]+)', 'ApiChangeset',
	'/api/0.6/changeset/([0-9]+)/upload', 'ApiChangesetUpload',
	'/api/0.6/changeset/([0-9]+)/close', 'ApiChangesetClose',
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



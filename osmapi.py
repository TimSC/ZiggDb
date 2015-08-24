# -*- coding: utf-8 -*-
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
	def __init__(self, ctx):
		self.lastIdsDb = ctx.lastIdsDb
		self.nodeIdToUuidDb = ctx.nodeIdToUuidDb
		self.uuidToNodeIdDb = ctx.uuidToNodeIdDb

		self.wayIdToUuidDb = ctx.wayIdToUuidDb
		self.uuidToWayIdDb = ctx.uuidToWayIdDb

		self.relationIdToUuidDb = ctx.relationIdToUuidDb
		self.uuidToRelationIdDb = ctx.uuidToRelationIdDb

	def AssignId(self, objType, uuid = None, subObject = None):

		cid = ""
		if uuid is not None:
			cid += uuid
		if subObject is not None:
			cid += subObject

		#Check if ID already assigned
		if objType == "node" and cid in self.uuidToNodeIdDb:
			return int(self.uuidToNodeIdDb[str(cid)])

		if objType == "way" and cid in self.uuidToWayIdDb:
			return int(self.uuidToWayIdDb[str(cid)])

		if objType == "relation" and cid in self.uuidToRelationIdDb:
			return int(self.uuidToRelationIdDb[str(cid)])

		#Assign a new ID
		newId = None
		if objType in self.lastIdsDb:
			newId = int(self.lastIdsDb[objType]) + 1
		else:
			newId = 1

		self.lastIdsDb[objType] = str(newId)

		if objType == "node":
			self.nodeIdToUuidDb[str(newId)] = str(cid)
			self.uuidToNodeIdDb[str(cid)] = str(newId)

		if objType == "way":
			self.wayIdToUuidDb[str(newId)] = str(cid)
			self.uuidToWayIdDb[str(cid)] = str(newId)

		if objType == "relation":
			self.relationIdToUuidDb[str(newId)] = str(cid)
			self.uuidToRelationIdDb[str(cid)] = str(newId)

		return newId

	def GetUuidFromId(self, objTy, objId):
		objIdStr = str(objId)

		if objTy == "node" and objIdStr in self.nodeIdToUuidDb:
			return self.nodeIdToUuidDb[objIdStr]

		if objTy == "way" and objIdStr in self.wayIdToUuidDb:
			return self.wayIdToUuidDb[objIdStr]

		if objTy == "relation" and objIdStr in self.relationIdToUuidDb:
			return self.relationIdToUuidDb[objIdStr]

		return None

def GetOsmIdForNonInts(idAssignment, objId, objType, subObject = None):
	if not isinstance(objId, int):
		return idAssignment.AssignId(objType, objId, subObject)
	return objId	

def ZiggToOsm(idAssignment, area):

	osmData = {"node": {}, "way": {}, "relation": {}}
	osmNodes = osmData["node"]
	osmWays = osmData["way"]
	osmRelations = osmData["relation"]

	#Write individual nodes to output
	for nodeId in area["nodes"]:
		objShapes, objData = area["nodes"][nodeId]
		shape = objShapes[0]
		outer, inners = shape
		pt = outer[0]
		nid = GetOsmIdForNonInts(idAssignment, nodeId, "node")

		osmNodes[nid] = (pt[:2], objData)

	#Write nodes that are part of other objects
	for objType in ["ways", "areas"]:
		objDict = area[objType]
		for objId in objDict:
			objShapes, objData = objDict[objId]
			shape = objShapes[0]
			outer, inners = shape
			for pt in outer:
				nodeId = pt[2]
				nid = GetOsmIdForNonInts(idAssignment, nodeId, "node")
				osmNodes[nid] = (pt[:2], {})

			if inners is None: continue
			for inner in inners:
				for pt in inner:
					nodeId = pt[2]
					nid = GetOsmIdForNonInts(idAssignment, nodeId, "node")
					osmNodes[nid] = (pt[:2], {})

	#Write ways
	for objId in area["ways"]:
		objShapes, objData = area["ways"][objId]
		shape = objShapes[0]
		outer, inners = shape
		oid = GetOsmIdForNonInts(idAssignment, objId, "way")

		nodeIds = []
		for pt in outer:
			nid = GetOsmIdForNonInts(idAssignment, pt[2], "node")
			nodeIds.append(nid)

		osmWays[oid] = (nodeIds, objData)

	#Convert areas to OSM shapes
	for objId in area["areas"]:
		objShapes, objData = area["areas"][objId]
		shape = objShapes[0]
		outer, inners = shape

		#Areas without inner polygons are treated as areas
		treatAsRelation = len(inners) > 0
		
		if treatAsRelation:
			#Write outer way
			wayOuterId = GetOsmIdForNonInts(idAssignment, objId, "way", "o")
			nodeIds = []
			for pt in outer:
				nodeIds.append(GetOsmIdForNonInts(idAssignment, pt[2], "node"))
			if len(outer) >= 2:
				nodeIds.append(GetOsmIdForNonInts(idAssignment, outer[0][2], "node")) #Close the area
			osmWays[wayOuterId] = (nodeIds, objData)

			#Writer inner ways
			wayInnersIds = []
			if inners is not None:
				for i, inner in enumerate(inners):
					oid = GetOsmIdForNonInts(idAssignment, objId, "way", "i{0}".format(i))
					nodeIds = []
					for pt in inner:
						nodeIds.append(GetOsmIdForNonInts(idAssignment, pt[2], "node"))
					if len(inner) >= 2: #Close the area
						nodeIds.append(GetOsmIdForNonInts(idAssignment, inner[0][2], "node"))
					osmWays[oid] = (nodeIds, objData)
					wayInnersIds.append(oid)

			oid = GetOsmIdForNonInts(idAssignment, objId, "relation")
			relationMembers = [[wayOuterId, "outer", "way"]]
			for wi in wayInnersIds:
				relationMembers.append([wi, "inner", "way"])
			objData["type"] = "multipolygon"
			osmRelations[oid] = (relationMembers, objData)
		else:
			#Convert area to closed way
			oid = GetOsmIdForNonInts(idAssignment, objId, "way")

			nodeIds = []
			for pt in outer:
				nid = GetOsmIdForNonInts(idAssignment, pt[2], "node")
				nodeIds.append(nid)
			if len(outer) >= 2:
				nodeIds.append(GetOsmIdForNonInts(idAssignment, outer[0][2], "node")) #Close the area

			osmWays[oid] = (nodeIds, objData)
			
	return osmData

def CheckObjTreatAsArea(objMems, objData):
	treatAsArea = False
	if objMems[0] == objMems[-1]: treatAsArea = True #Lowest precidence rule

	for key in ["highway", "aerialway", "barrier", 
			"boundary", "cycleway", "railway", 
			"route", "waterway", "addr:"]:
		if key in objData: treatAsArea = False
	
	for key in ["landuse"]:
		if key in objData: treatAsArea = True

	if "area" in objData:	
		if objData["area"].lower() in ["yes", 1, "true"]: treatAsArea = True
		if objData["area"].lower() in ["no", 0, "false"]: treatAsArea = False #Highest precidence rule
	return treatAsArea

def OsmToZigg(idAssignment, osmData):

	#Conversion of areas between representations
	#OSM representation	             Zigg representation   OSM representation
	#
	#Unclosed way -----------------> ways ---------------> unclosed way
	#
	#Closed ways ----> check tags -> ways ---------------> closed ways
	#                    |                       |
	#                    └---------> areas ------┘ (no inner polygons)
	#
	#Multipolygons ----------------> areas --------------> multipolygons

	area = {"nodes": {}, "ways": {}, "areas": {}}
	ziggAreas = area["areas"]
	ziggWays = area["ways"]
	ziggNodes = area["nodes"]
	accounted = {"node": set(), "way": set(), "relation": set()}

	#Relations to areas
	for oid in osmData["relation"]:
		objMems, objData = osmData["relation"][oid]
		if oid > 0:
			relUuid = idAssignment.GetUuidFromId("relation", oid)
			if relUuid is None: raise ValueError("Unknown relation")
		else:
			relUuid = oid

		if "type" not in objData or objData["type"] != "multipolygon":
			continue
		outers = []
		inners = []
		for memId, memRole, memType in objMems:
			if memType != "way": continue

			try:
				wayMems, wayData = osmData["way"][memId]
			except KeyError:
				raise RuntimeError("Way data missing from internal calculation")
			wayShape = []
			for pt in wayMems:
				try:
					ptShape, ptData = osmData["node"][pt]
				except KeyError:
					raise RuntimeError("Node data missing from internal calculation")
				if pt > 0:
					ptUuid = idAssignment.GetUuidFromId("node", pt)
					if ptUuid is None: raise ValueError("Unknown node")
				else:
					ptUuid = pt
				wayShape.append([ptShape[0], ptShape[1], ptUuid])
				if len(ptData) == 0:
					accounted["node"].add(pt)
				
			if memRole == "inner":
				inners.append(wayShape)
			if memRole == "outer":
				outers.append(wayShape)
			accounted["way"].add(memId)
	
		if len(outers) > 1:
			raise ValueError("Multiple outer ways not implemented")
		if len(outers) == 0:
			raise ValueError("No outer way defined")
		objDataCopy = objData.copy()
		del objDataCopy["type"]
		#TODO validate areas are ok (inner polygons are within outer polygon)

		ziggAreas[relUuid] = [[[outers[0], inners]], objDataCopy]
		accounted["relation"].add(oid)

	#Process closed ways (and other special cases) to areas
	for oid in osmData["way"]:
		if oid in accounted["way"]: continue
		objMems, objData = osmData["way"][oid]
		if len(objMems) < 2: continue
		treatAsArea = CheckObjTreatAsArea(objMems, objData)
		if not treatAsArea: continue

		if oid > 0:
			wayUuid = idAssignment.GetUuidFromId("way", oid)
			if wayUuid is None: raise ValueError("Unknown way")
		else:
			wayUuid = oid
		
		wayShape = []
		for pt in objMems[:-1]: #Omit last node because areas are assumed to do that anyway
			try:
				ptShape, ptData = osmData["node"][pt]
			except KeyError:
				raise RuntimeError("Node data missing from internal calculation")
			if pt > 0:
				ptUuid = idAssignment.GetUuidFromId("node", pt)
				if ptUuid is None: raise ValueError("Unknown node")
			else:
				ptUuid = pt
			wayShape.append([ptShape[0], ptShape[1], ptUuid])
			if len(ptData) == 0:
				accounted["node"].add(pt)

		ziggAreas[wayUuid] = [[[wayShape, []]], objData]
		accounted["way"].add(oid)

	#Process remaining ways
	for oid in osmData["way"]:
		if oid in accounted["way"]: continue
		objMems, objData = osmData["way"][oid]
		if oid > 0:
			wayUuid = idAssignment.GetUuidFromId("way", oid)
			if wayUuid is None: raise ValueError("Unknown way")
		else:
			wayUuid = oid
		
		wayShape = []
		for pt in objMems:
			try:
				ptShape, ptData = osmData["node"][pt]
			except KeyError:
				raise RuntimeError("Node data missing from internal calculation")
			if pt > 0:
				ptUuid = idAssignment.GetUuidFromId("node", pt)
				if ptUuid is None: raise ValueError("Unknown node")
			else:
				ptUuid = pt
			wayShape.append([ptShape[0], ptShape[1], ptUuid])
			if len(ptData) == 0:
				accounted["node"].add(pt)

		ziggWays[wayUuid] = [[[wayShape, None]], objData]
		accounted["way"].add(oid)

	#Process remaining nodes
	for oid in osmData["node"]:
		if oid in accounted["node"]: continue
		pt, objData = osmData["node"][oid]
		if oid > 0:
			nodeUuid = idAssignment.GetUuidFromId("node", oid)
			if nodeUuid is None: raise ValueError("Unknown node")
		else:
			nodeUuid = oid

		ziggNodes[nodeUuid] = [[[[[pt[0], pt[1], nodeUuid]], None]], objData]
		accounted["node"].add(oid)

	return area

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
		nodePosDb = web.ctx.nodePosDb
		wayDb = web.ctx.wayDb
		idAssignment = IdAssignment(web.ctx)
		writeOldPos = False
		debug = 0
		if "debug" in webInput:
			debug = int(webInput["debug"])

		bbox = map(float, webInput["bbox"].split(","))
		area = ziggDb.GetArea(bbox, debug)
		nodesWritten = set()

		out = [u"<?xml version='1.0' encoding='UTF-8'?>\n"]
		out.append(u"<osm version='0.6' upload='true' generator='ZiggDb'>\n")
  		out.append(u"<bounds minlat='{0}' minlon='{1}' maxlat='{2}' maxlon='{3}' origin='ZiggDb' />".format(
			bbox[1], bbox[0], bbox[3], bbox[2]))

		osmData = ZiggToOsm(idAssignment, area)

		#Debug code, try the inverse function
		#OsmToZigg(idAssignment, osmData)

		#Write individual nodes to output
		for nid in osmData["node"]:
			objPt, objData = osmData["node"][nid]

			out.append(u"<node id='{0}' timestamp='2006-11-30T00:03:33Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1' lat='{1}' lon='{2}'>\n".format(nid, objPt[0], objPt[1]))
			for key in objData:
				out.append(u"  <tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))

			if writeOldPos:
				out.append(u"<tag k='_old_lat' v='{0}' />\n".format(objPt[0]))
				out.append(u"<tag k='_old_lon' v='{0}' />\n".format(objPt[1]))
			out.append(u"</node>\n")

			nodePosDb[nid] = objPt

		#Write ways
		for oid in osmData["way"]:
			nodeIds, objData = osmData["way"][oid]
		
			out.append(u"<way id='{0}' timestamp='2011-12-14T18:14:58Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(oid))
			for nid in nodeIds:
				out.append(u"<nd ref='{0}' />\n".format(nid))
			for key in objData:
				out.append(u"<tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
			out.append(u"</way>\n")

			wayDb[oid] = [nodeIds, None]

		#Write relations
		for oid in osmData["relation"]:
			objMembers, objData = osmData["relation"][oid]

			out.append(u"<relation id='{0}' timestamp='2008-03-10T17:43:07Z' uid='1' user='ZiggDb' visible='true' version='1' changeset='1'>\n".format(
				oid))
			for memId, memRole, memType in objMembers:
				out.append(u"  <member type='{2}' ref='{0}' role='{1}' />\n".format(memId, escape(memRole), memType))

			for key in objData:
				out.append(u"  <tag k='{0}' v='{1}' />\n".format(escape(key), escape(objData[key])))
			out.append(u"</relation>\n")

		out.append(u"</osm>\n")

		web.header('Content-Type', 'text/xml')
		return "".join(out).encode("utf-8")

class ApiGetObject(object):
	def GET(self, objId):
		#Add a global lock TODO
		return self.Render(int(objId))

	def POST(self, objId):
		#Add a global lock TODO
		return self.Render(int(objId))

	def Render(self, objId):
		webInput = web.input()
		ziggDb = web.ctx.ziggDb
		nodePosDb = web.ctx.nodePosDb
		wayDb = web.ctx.wayDb
		idAssignment = IdAssignment(web.ctx)
		writeOldPos = False
		debug = 0
		if "debug" in webInput:
			debug = int(webInput["debug"])
		bbox = None
		if "bbox" in webInput:
			bbox = map(float, webInput["bbox"].split(","))

		nuuid = idAssignment.GetUuidFromId("way", objId)	

		result = ziggDb.CheckForObject(bbox, nuuid, debug)
		return "".join(result).encode("utf-8")

class ApiVerifyCache(object):
	def GET(self):
		#Add a global lock TODO
		return self.Render()

	def POST(self):
		#Add a global lock TODO
		return self.Render()

	def Render(self):
		webInput = web.input()
		ziggDb = web.ctx.ziggDb
		nodePosDb = web.ctx.nodePosDb
		wayDb = web.ctx.wayDb
		idAssignment = IdAssignment(web.ctx)

		bbox = map(float, webInput["bbox"].split(","))
		area = ziggDb.GetArea(bbox)
		osmData = ZiggToOsm(idAssignment, area)

		out = []
		for nid in osmData["node"]:
			try:
				cachedNode = nodePosDb[nid]
			except KeyError:
				continue

			pos, data = osmData["node"][nid]
			diff1 = abs(cachedNode[0] - pos[0]) < 1e-7
			diff2 = abs(cachedNode[1] - pos[1]) < 1e-7
			if diff1 is True and diff2 is True:
				continue

			out.append("Error: node position incorrect {0} {1}\n".format(diff1, diff2))

		for wid in osmData["way"]:
			try:
				cachedNode = wayDb[wid]
			except KeyError:
				continue

			childNds, tags = osmData["way"][wid]
			if childNds == cachedNode[0]:
				continue

			out.append("Way has incorrect nodes {0} {1} {2}\n".format(wid, childNds, cachedNode[0]))

		return "".join(out)

class ApiVerifyDb(object):
	def GET(self):
		#Add a global lock TODO
		return self.Render()

	def POST(self):
		#Add a global lock TODO
		return self.Render()

	def Render(self):
		webInput = web.input()
		ziggDb = web.ctx.ziggDb
		idAssignment = IdAssignment(web.ctx)
		bbox = map(float, webInput["bbox"].split(","))

		return ziggDb.Verify(bbox)

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
		idAssignment = IdAssignment(web.ctx)
		cid = idAssignment.AssignId("changeset")
		webInput = web.input()
		webData = web.data()

		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "logs/{0}.txt".format(requestNum)), "wt")
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
		idAssignment = IdAssignment(web.ctx)
		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "logs/{0}.txt".format(requestNum)), "wt")
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
		idAssignment = IdAssignment(web.ctx)

		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "logs/{0}.txt".format(requestNum)), "wt")
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

	def GET(self, cid):
		return None #Not allowed

	def POST(self, cid):
		return self.Render(cid)

	def Render(self, cid):
		idAssignment = IdAssignment(web.ctx)
		webData = web.data()
		nodePosDb = web.ctx.nodePosDb
		wayDb = web.ctx.wayDb
		ziggDb = web.ctx.ziggDb
		webInput = web.input()
		debug = 0
		if "debug" in webInput:
			debug = int(webInput["debug"])
		debug2 = 0
		if "debug2" in webInput:
			debug2 = webInput["debug2"]

		activeArea = [None, None, None, None]

		logging = True
		if logging:
			requestNum = idAssignment.AssignId("request")
			curdir = os.path.dirname(__file__)
			fi = open(os.path.join(curdir, "logs/{0}.txt".format(requestNum)), "wt")
			webInput = web.input()
			fi.write(str(self.__class__.__name__)+"\n")
			fi.write(str(webInput)+"\n")
			fi.write(str(cid)+"\n")
			fi.write(str(web.ctx.env.copy())+"\n")
			fi.write(str(web.data())+"\n")

		#Preprocess data to determine active area
		root = ET.fromstring(webData)
		for meth in root:
			method = meth.tag
			for el in meth:
				objTy = el.tag
				objId = int(el.attrib["id"])
				objCid = int(el.attrib["changeset"])

				#Get current node positions and update active area
				if objTy == "node":
					if "lat" in el.attrib and "lat" in el.attrib:
						objLat = float(el.attrib["lat"])
						objLon = float(el.attrib["lon"])
		
						zigg.UpdateBbox(activeArea, [objLat, objLon])

					nid = int(el.attrib["id"])
					if nid >= 0: 
						#Ignore negative nodes since they have no original position
						pos = nodePosDb[nid]
					
						zigg.UpdateBbox(activeArea, pos[:2])

				tagDict = {}
				for ch in el:
					if ch.tag != "tag": continue
					tagDict[ch.attrib["k"]] = ch.attrib["v"]

				#Get way members when explicitly listed in upload
				for ch in el:
					if ch.tag != "nd": continue
					nid = int(ch.attrib["ref"])
					if nid < 0: continue #Ignore negative nodes since they have no original position
					pos = nodePosDb[nid]
					zigg.UpdateBbox(activeArea, pos)

				#Deleting objects requires us to get the relevant children
				if method == "delete" and objTy == "way" and objId > 0:
					if objId not in wayDb:
						raise RuntimeError("Way not in OSM cache")
					nodesInWay = wayDb[objId][0]

					for nid in nodesInWay:
						nPos = nodePosDb[int(nid)]
						zigg.UpdateBbox(activeArea, nPos)

				#Get nodes in relation (not sure if this is really meaningful with incomplete 
				#implementation - what about ways?)
				for ch in el:
					if ch.tag != "member": continue
					if ch.attrib["type"] != "node": continue

					nid = int(ch.attrib["ref"])
					if nid < 0: continue #Ignore negative nodes since they have no original position
					pos = nodePosDb[nid]
					zigg.UpdateBbox(activeArea, pos)

		if logging:
			fi.write("Unpadded"+str(activeArea)+"\n")
			fi.flush()

		if 0:
			#Pad active area with margin to prevent critical nodes on the edge
			#This avoids numerical stability problems
			#left,bottom,right,top
			activeArea[0] -= 1e-5
			activeArea[1] -= 1e-5
			activeArea[2] += 1e-5
			activeArea[3] += 1e-5
			if activeArea[0] < -180.: activeArea[0] = -180.
			if activeArea[1] < -90.: activeArea[1] = -90.
			if activeArea[2] > 180.: activeArea[2] = 180.
			if activeArea[3] > 90.: activeArea[3] = 90.
	
			if logging:
				fi.write("Padded"+str(activeArea)+"\n")
				fi.flush()
	
		if None in activeArea:
			raise RuntimeError("Invalid bbox")

		#Retrieve active area
		activeData = ziggDb.GetArea(activeArea, debug)

		#Convert active area to osm style representation
		osmData = ZiggToOsm(idAssignment, activeData)

		if logging:
			fi.write("Active area nodes {0}\n".format(len(activeData["nodes"])))
			fi.write("Active area ways {0}\n".format(len(activeData["ways"])))
			fi.write("Active area areas {0}\n".format(len(activeData["areas"])))
			fi.flush()

		#Apply changes to OSM representation of active data
		newObjs = {'nodes': {}, 'ways': {}, 'relations': {}}
		modObjs = {'nodes': {}, 'ways': {}, 'relations': {}}
		delObjs = {'nodes': set(), 'ways': set(), 'relations': set()}

		if logging:
			fi.write(str(activeData)+"\n")

		for meth in root:
			method = meth.tag
			if method == "create":

				#Find data that creates new nodes
				for el in meth:
					if el.tag != "node": continue
					objId = int(el.attrib["id"])
					if objId >= 0: continue
					objLat = float(el.attrib["lat"])
					objLon = float(el.attrib["lon"])

					tagDict = {}
					for ch in el:
						if ch.tag != "tag": continue
						tagDict[ch.attrib["k"]] = ch.attrib["v"]

					newObjs["nodes"][objId] = [objLat, objLon, tagDict]

				#Find data that creates new ways
				for el in meth:
					if el.tag != "way": continue
					objId = int(el.attrib["id"])
					if objId >= 0: continue

					memNds = []
					tagDict = {}
					for ch in el:
						if ch.tag == "tag":
							tagDict[ch.attrib["k"]] = ch.attrib["v"]
						if ch.tag == "nd":
							memNds.append(int(ch.attrib["ref"]))

					newObjs["ways"][objId] = [memNds, tagDict]

				#Find data that creates new relations
				for el in meth:
					if el.tag != "relation": continue
					objId = int(el.attrib["id"])
					if objId >= 0: continue

					members = []
					tagDict = {}
					for ch in el:
						if ch.tag == "tag":
							tagDict[ch.attrib["k"]] = ch.attrib["v"]
						if ch.tag == "member":
							mty = ch.attrib["ref"]
							mref = int(ch.attrib["ref"])
							mrole = ch.attrib["role"]
							members.append((mref, mrole, mty))

					newObjs["relations"][objId] = [members, tagDict]

				#Apply new nodes change to database
				for nid in newObjs["nodes"]:
					objLat, objLon, tagDict = newObjs["nodes"][nid]
					osmData["node"][nid] = [(objLat, objLon, nid), tagDict]
				
				#Apply new way changes to database
				for wid in newObjs["ways"]:
					memNds, tagDict = newObjs["ways"][wid]
					osmData["way"][wid] = [memNds, tagDict]

				#Apply new relation changes to database
				for oid in newObjs["relations"]:
					members, tagDict = newObjs["relations"][oid]
					osmData["relation"][oid] = [members, tagDict]

			if method == "modify":
				
				#Find data that modifies nodes
				for el in meth:
					if el.tag != "node": continue
					objId = int(el.attrib["id"])
					if objId < 0: continue
					objLat = float(el.attrib["lat"])
					objLon = float(el.attrib["lon"])
					objVer = int(el.attrib["version"])

					#Find uuid of node
					nuuid = idAssignment.GetUuidFromId("node", objId)			
					if nuuid is None: 
						raise RuntimeError("Unknown node {0} in upload".format(objId))
			
					tagDict = {}
					for ch in el:
						if ch.tag != "tag": continue
						tagDict[ch.attrib["k"]] = ch.attrib["v"]

					modObjs["nodes"][objId] = [objLat, objLon, tagDict, objVer]

				#Find data that modifies existing ways
				for el in meth:
					if el.tag != "way": continue
					objId = int(el.attrib["id"])
					if objId < 0: continue
					objVer = int(el.attrib["version"])

					memNds = []
					tagDict = {}
					for ch in el:
						if ch.tag == "tag":
							tagDict[ch.attrib["k"]] = ch.attrib["v"]
						if ch.tag == "nd":
							memNds.append(int(ch.attrib["ref"]))

					modObjs["ways"][objId] = [memNds, tagDict, objVer]

				#Apply changes to database
				for nid in modObjs["nodes"]:
					objLat, objLon, tagDict, objVer = modObjs["nodes"][nid]
					osmData["node"][nid] = [(objLat, objLon, nid), tagDict]

				for wid in modObjs["ways"]:
					memNds, tagDict, objVer = modObjs["ways"][wid]
					osmData["way"][wid] = [memNds, tagDict]

			if method == "delete":
				
				#Find data that deletes existing nodes
				for el in meth:
					if el.tag != "node": continue
					objId = int(el.attrib["id"])
					if objId < 0: continue

					#Find uuid of node
					nuuid = idAssignment.GetUuidFromId("node", objId)			
					if nuuid is None: 
						raise RuntimeError("Unknown node {0} in upload".format(objId))
			
					tagDict = {}
					for ch in el:
						if ch.tag != "tag": continue
						tagDict[ch.attrib["k"]] = ch.attrib["v"]

					delObjs["nodes"].add(objId)

				#Find data that deletes existing ways
				for el in meth:
					if el.tag != "way": continue
					objId = int(el.attrib["id"])
					if objId < 0: continue

					#Find uuid of way
					nuuid = idAssignment.GetUuidFromId("way", objId)			
					if nuuid is None: 
						raise RuntimeError("Unknown way {0} in upload".format(objId))

					delObjs["ways"].add(objId)

				#Apply change to database
				for nid in delObjs["nodes"]:
					del osmData["node"][nid]

				for wid in delObjs["ways"]:
					del osmData["way"][wid]

		#Convert OSM representation to zigg based format
		updatedArea = OsmToZigg(idAssignment, osmData)

		if logging:
			fi.write(str(updatedArea)+"\n")

		#Copy active bbox to updated data
		updatedArea["active"] = activeArea
		updatedArea["versionInfo"] = activeData["versionInfo"]

		#Update database with new data
		userInfo = {}
		idDiff = ziggDb.SetArea(updatedArea, userInfo, debug)
		
		#Return updated IDs to client
		out = []
		out.append(u'<?xml version="1.0" encoding="UTF-8"?>\n')
		out.append(u'<diffResult generator="ZiggDb" version="0.6">\n')
		for nid in idDiff["nodes"]:
			nuuid = idDiff["nodes"][nid]
			#oldOld, newNew
			newId = idAssignment.AssignId("node", nuuid)
			modTag = []
			modTag.append(u'<node old_id="{0}" new_id="{1}"'.format(nid, newId))
			newVer = 1
			if newVer is not None:
				modTag.append(u' new_version="{0}"'.format(newVer))
			modTag.append(u'/>\n')
			out.append("".join(modTag))

		for wid in idDiff["ways"]:
			nuuid = idDiff["ways"][wid]
			newId = idAssignment.AssignId("way", nuuid)
			modTag = []
			modTag.append(u'<way old_id="{0}" new_id="{1}"'.format(wid, newId))
			newVer = 1
			if newVer is not None:
				modTag.append(u' new_version="{0}"'.format(newVer))
			modTag.append(u'/>\n')
			out.append("".join(modTag))

		for wid in idDiff["areas"]:
			nuuid = idDiff["areas"][wid]
			newId = idAssignment.AssignId("way", nuuid)
			modTag = []
			modTag.append(u'<way old_id="{0}" new_id="{1}"'.format(wid, newId))
			newVer = 1
			if newVer is not None:
				modTag.append(u' new_version="{0}"'.format(newVer))
			modTag.append(u'/>\n')
			out.append("".join(modTag))

		for nid in modObjs["nodes"]:
			nodeInfo = modObjs["nodes"][nid]
			out.append(u'<node old_id="{0}" new_id="{0}" new_version="{1}"/>\n'.format(nid, nodeInfo[3]+1))

		for wid in modObjs["ways"]:
			wayInfo = modObjs["ways"][wid]
			out.append(u'<way old_id="{0}" new_id="{0}" new_version="{1}"/>\n'.format(wid, wayInfo[2]+1))

		#TODO update relation members

		for nid in delObjs["nodes"]:
			out.append(u'<node old_id="{0}"/>\n'.format(nid))

		for wid in delObjs["ways"]:
			out.append(u'<way old_id="{0}"/>\n'.format(wid))

		#TODO update relation members

		if logging:
			fi.write("modObjs: {0}\n".format(modObjs))
			fi.write("delObjs: {0}\n".format(delObjs))

		out.append(u'</diffResult>\n')

		#Update child object IDs in changes
		for wid in newObjs["ways"]:
			memNds, tagDict = newObjs["ways"][wid]
			#nuuid = idDiff["ways"][wid]
			updatedMemNds = []
			for nid in memNds:
				if nid < 0:
					cnuuid = idDiff["nodes"][nid]
					cnewId = idAssignment.AssignId("node", cnuuid)
					updatedMemNds.append(cnewId)
				else:
					updatedMemNds.append(nid)
			newObjs["ways"][wid][0] = updatedMemNds

		for wid in modObjs["ways"]:
			memNds, tagDict, objVer = modObjs["ways"][wid]
			#nuuid = idDiff["ways"][wid]
			updatedMemNds = []
			for nid in memNds:
				if nid < 0:
					cnuuid = idDiff["nodes"][nid]
					cnewId = idAssignment.AssignId("node", cnuuid)
					updatedMemNds.append(cnewId)
				else:
					updatedMemNds.append(nid)
			modObjs["ways"][wid][0] = updatedMemNds

		#TODO update relation members

		#Update object cache with created objects
		newNodePosDict = {}
		for nid in newObjs["nodes"]:
			objLat, objLon, tagDict = newObjs["nodes"][nid]
			nuuid = idDiff["nodes"][nid]
			newId = idAssignment.AssignId("node", nuuid)
			nodePosDb[newId] = [objLat, objLon, nuuid]

		for wid in newObjs["ways"]:
			memNds, tagDict = newObjs["ways"][wid]
			if wid in idDiff["ways"]:
				nuuid = idDiff["ways"][wid]
			else:
				nuuid = idDiff["areas"][wid]
			newId = idAssignment.AssignId("way", nuuid)
			wayDb[newId] = [memNds, nuuid]

		for oid in newObjs["relations"]:
			members, tagDict = newObjs["relations"][oid]
			nuuid = idDiff["areas"][oid]
			newId = idAssignment.AssignId("relation", nuuid)
			relationDb[newId] = [members, nuuid]

		#Update object cache with modified objects
		for nid in modObjs["nodes"]:
			objLat, objLon, tagDict, objVer = modObjs["nodes"][nid]
			nuuid = idAssignment.GetUuidFromId("node", nid)
			nodePosDb[nid] = [objLat, objLon, nuuid]

		for wid in modObjs["ways"]:
			memNds, tagDict, objVer = modObjs["ways"][wid]
			wuuid = idAssignment.GetUuidFromId("way", wid)
			wayDb[wid] = [memNds, wuuid]

		#TODO process relations

		#Delete obj in cache when necessary
		for nid in delObjs["nodes"]:
			del nodePosDb[nid]

		for wid in delObjs["ways"]:
			del wayDb[wid]

		#TODO process relations

		if logging:
			fi.write("response:\n")
			fi.write("".join(out).encode("utf-8")+"\n")
			fi.close()

		#Return result
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
		idAssignment = IdAssignment(web.ctx)

		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "logs/{0}.txt".format(requestNum)), "wt")
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

		idAssignment = IdAssignment(web.ctx)
		requestNum = idAssignment.AssignId("request")
		curdir = os.path.dirname(__file__)
		fi = open(os.path.join(curdir, "logs/{0}.txt".format(requestNum)), "wt")
		webInput = web.input()
		fi.write(str(self.__class__.__name__)+"\n")
		fi.write(str(webInput))
		fi.close()

		web.header('Content-Type', 'text/xml')
		return u"".join(out).encode("utf-8")

urls = (
	'/api/0.6/map', 'ApiMap',
	'/api/0.6/verifycache', 'ApiVerifyCache',
	'/api/0.6/verifydb', 'ApiVerifyDb',
	'/api/capabilities', 'ApiCapabilities',
	'/api/0.6/capabilities', 'ApiCapabilities',
	'/api/0.6/changeset/create', 'ApiChangesetCreate',
	'/api/0.6/user/details', 'ApiUserDetails',
	'/api/0.6/changesets', 'ApiChangesets',
	'/api/0.6/changeset/([0-9]+)', 'ApiChangeset',
	'/api/0.6/changeset/([0-9]+)/upload', 'ApiChangesetUpload',
	'/api/0.6/changeset/([0-9]+)/close', 'ApiChangesetClose',
	'/api/0.6/way/([0-9]+)', 'ApiGetObject',
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

def OpenOsmDatabaseHandles(ctx):
	dataFolder = os.path.join(curdir, 'data')
	if not os.path.exists(dataFolder):
		try:
			os.makedirs(dataFolder)
		except:
			pass
	ctx.nodeIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'nodeIdToUuidDb.sqlite'), autocommit=True)
	ctx.uuidToNodeIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToNodeIdDb.sqlite'), autocommit=True)
	ctx.nodePosDb = SqliteDict(os.path.join(curdir, 'data', 'nodePosDb.sqlite'), autocommit=True)
	ctx.wayDb = SqliteDict(os.path.join(curdir, 'data', 'wayDb.sqlite'), autocommit=True)
	ctx.relationDb = SqliteDict(os.path.join(curdir, 'data', 'relationDb.sqlite'), autocommit=True)

	ctx.wayIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'wayIdToUuidDb.sqlite'), autocommit=True)
	ctx.uuidToWayIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToWayIdDb.sqlite'), autocommit=True)
	ctx.relationIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'relationIdToUuidDb.sqlite'), autocommit=True)
	ctx.uuidToRelationIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToRelationIdDb.sqlite'), autocommit=True)

	ctx.lastIdsDb = SqliteDict(os.path.join(curdir, 'data', 'lastIdsDb.sqlite'), autocommit=True)

def InitDatabaseConn():
	curdir = os.path.dirname(__file__)
	
	OpenOsmDatabaseHandles(web.ctx)
	web.ctx.ziggDb = zigg.ZiggDb(config.repos, curdir)
	#web.ctx.session = session

web.config.debug = 1
app = web.application(urls, globals())
curdir = os.path.dirname(__file__)
app.add_processor(web.loadhook(InitDatabaseConn))

#session = web.session.Session(app, web.session.DiskStore(os.path.join(curdir,'sessions')),)

application = app.wsgifunc()



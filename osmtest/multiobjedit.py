import sys, conf
sys.path.append( "." )
from urlutil import *
import xml.etree.ElementTree as ET
from sqlitedict import SqliteDict
from xml.sax.saxutils import quoteattr

def InterpretUploadResponse(response):
	root = ET.fromstring(response)
	if root.tag == "html":
		raise RuntimeError("Unexpected html in response")
	diff = {"node": {}, "way": {}, "relation": {}}
	for el in root:
		val = {}
		for k in el.attrib:
			val[k] = int(el.attrib[k])
		diff[el.tag][int(el.attrib["old_id"])] = val
	return diff

def InterpretDownloadedArea(downloadedData):
	root = ET.fromstring(downloadedData)
	if root.tag == "html":
		raise RuntimeError("Unexpected html in response")
	data = {"node": {}, "way": {}, "relation": {}}
	for el in root:
		objTy = el.tag
		if objTy == "bounds": 
			continue
		data[objTy][int(el.attrib["id"])] = el		
	return data

def ExtractTags(xmlObj):
	out = {}
	for el in xmlObj:
		if el.tag != "tag": continue
		out[el.attrib["k"]] = el.attrib["v"]
	return out

def CheckWayHasChildNodes(wayXml, nodeIds):
	tmp = set()
	for el in wayXml:
		if el.tag != "nd": continue
		tmp.add(int(el.attrib["ref"]))
	for nid in nodeIds:
		if int(nid) not in tmp:
			return False
	return True

def CheckNodePosition(nodeXml, lat, lon):
	return abs(float(nodeXml.attrib["lat"]) - lat) < 1e-7 and abs(float(nodeXml.attrib["lon"]) - lon) < 1e-7

def DeleteSingleNode(nid, cid, userpass, lat, lon, save, verbose=0):
	if verbose>=1: print "Delete node", nid
	deleteNode = '<osmChange version="0.6" generator="JOSM">' +\
	"<delete>\n" +\
	"  <node id='"+str(nid)+"' version='1' "+\
	"changeset='"+str(cid)+"' lat='"+str(lat)+"' lon='"+str(lon)+"' />\n"+\
	"</delete>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteNode,userpass)
	if verbose>=2: print response
	if save: open("del.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")
	diff = InterpretUploadResponse(response[0])
	return (1, "OK")

def TestMultiObjectEditing(userpass, verbose=0, save=False):

	log = open("log.txt", "wt")

	# ********** Create a way with two nodes ***************
	if verbose>=1: print "Open changeset"
	#Create a changeset
	createChangeset = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	"<osm version='0.6' generator='JOSM'>\n" +\
	"  <changeset  id='0' open='false'>\n" +\
	"    <tag k='comment' v='python test function' />\n" +\
	"    <tag k='created_by' v='JOSM/1.5 (3592 en_GB)' />\n" +\
	"  </changeset>\n" +\
	"</osm>\n"

	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if save: open("open.html", "wt").write(response[0])
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changeset")

	lat = [51.25022331526812, 51.2419166618214]
	lon = [-0.6042092878597837, -0.5910182209303836]

	if verbose>=1: print "Create way between two nodes"
	#Create a way between two nodes
	create = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	"<osmChange version='0.6' generator='JOSM'>\n" +\
	"<create version='0.6' generator='JOSM'>\n" +\
	"  <node id='-289' changeset='{0}' lat='{1}' lon='{2}' />\n".format(cid, lat[0], lon[0]) +\
	"  <node id='-2008' changeset='{0}' lat='{1}' lon='{2}' />\n".format(cid, lat[1], lon[1])+\
	"  <way id='-2010' changeset='"+str(cid)+"'>\n"+\
	"    <nd ref='-289' />\n"+\
	"    <nd ref='-2008' />\n"+\
	"  </way>\n"+\
	"</create>\n" +\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",create,userpass)
	if verbose>=2: print response
	if save: open("add.html", "wt").write(response[0])
	if log is not None: 
		log.write(response[1])
		log.write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating node")
	
	diff = InterpretUploadResponse(response[0])
	nodeId1 = int(diff["node"][-289]["new_id"])
	nodeId2 = int(diff["node"][-2008]["new_id"])
	wayId = int(diff["way"][-2010]["new_id"])

	if verbose>=1: print "Close changeset"
	#Close the changeset
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	#Read back area containing data
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	if save: open("response.html", "wt").write(response[0])
	data = InterpretDownloadedArea(response[0])
	node1Readback = data["node"][nodeId1]
	if not CheckNodePosition(node1Readback, lat[0], lon[0]):
		return (0,"Error node has bad position")
	node2Readback = data["node"][nodeId2]
	if not CheckNodePosition(node2Readback, lat[1], lon[1]):
		return (0,"Error node has bad position")
	wayReadback = data["way"][wayId]
	if not CheckWayHasChildNodes(wayReadback, [nodeId1, nodeId2]):
		return (0,"Error way has incorrect child nodes")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]
	if save: open("verify.html", "wt").write(response[0])

	#***************** Translate a node within a way ******************

	if verbose>=1: print "Open changeset"
	#Open another changeset
	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changset")

	if verbose>=1: print "Modify (by translation) a node with id:", nodeId1
	#Modify test node
	lat.append(51.25)
	lon.append(-0.60)
	modifyNode = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<modify>\n"+\
	"  <node id='"+str(nodeId1)+"' version='1' changeset='"+str(cid)+"' lat='"+str(lat[2])+"' lon='"+str(lon[2])+"' />\n"+\
	"</modify>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",modifyNode,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error modifying node")
	diff = InterpretUploadResponse(response[0])

	#Close changeset
	if verbose>=1: print "Close changeset"
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	#Read back area containing data
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	data = InterpretDownloadedArea(response[0])
	node1Readback = data["node"][nodeId1]
	if not CheckNodePosition(node1Readback, lat[2], lon[2]):
		return (0,"Error node has bad position")
	node2Readback = data["node"][nodeId2]
	wayReadback = data["way"][wayId]
	if not CheckWayHasChildNodes(wayReadback, [nodeId1, nodeId2]):
		return (0,"Error way has incorrect child nodes")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]
	if save: open("verify.html", "wt").write(response[0])

	#**************** Modify way's tags *********************

	if verbose>=1: print "Open changeset"
	#Open another changeset
	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changset")

	if verbose>=1: print "Modify (by changing tags) a way with id:", wayId
	#Modify way tags
	modifyNode = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<modify>\n"+\
	"  <way id='{0}' changeset='{1}' version='{2}'>\n".format(wayId, cid, 1)+\
	"    <nd ref='{0}' />\n".format(nodeId1)+\
	"    <nd ref='{0}' />\n".format(nodeId2)+\
	"    <tag k='foo' v='bar'/>\n"+\
	"  </way>\n"+\
	"</modify>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",modifyNode,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error modifying way")
	diff = InterpretUploadResponse(response[0])
	wayDiff = diff["way"][wayId]

	#Close changeset
	if verbose>=1: print "Close changeset"
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	#Read back area containing data
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	data = InterpretDownloadedArea(response[0])
	node1Readback = data["node"][nodeId1]
	if not CheckNodePosition(node1Readback, lat[2], lon[2]):
		return (0,"Error node has bad position")
	node2Readback = data["node"][nodeId2]
	wayReadback = data["way"][wayId]
	if not CheckWayHasChildNodes(wayReadback, [nodeId1, nodeId2]):
		return (0,"Error way has incorrect child nodes")
	wayTags = ExtractTags(wayReadback)
	if "foo" not in wayTags or wayTags["foo"] != "bar": 
		return (0,"Error way has incorrect tag")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]
	if save: open("verify.html", "wt").write(response[0])

	#************* Modify child nodes of a way ******************

	if verbose>=1: print "Open changeset"
	#Open another changeset
	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changset")

	if verbose>=1: print "Add an extra node"
	#Add another test node
	lat.append(51.55)
	lon.append(-0.59)
	modifyNode = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<create>\n"+\
	"  <node id='-105' version='1' changeset='"+str(cid)+"' lat='"+str(lat[3])+"' lon='"+str(lon[3])+"' />\n"+\
	"</create>\n"+\
	"<modify>\n"+\
	"  <way id='{0}' changeset='{1}' version='{2}'>\n".format(wayId, cid, 1)+\
	"    <nd ref='{0}' />\n".format(nodeId1)+\
	"    <nd ref='{0}' />\n".format(nodeId2)+\
	"    <nd ref='-105' />\n"+\
	"    <tag k='foo2' v='bar'/>\n"+\
	"  </way>\n"+\
	"</modify>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",modifyNode,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error modifying way")
	diff = InterpretUploadResponse(response[0])
	wayDiff = diff["way"][wayId]
	nodeId3 = int(diff["node"][-105]["new_id"])

	#wayDb = SqliteDict('../data/wayDb.sqlite', autocommit=True)
	#print wayDb[wayId]

	#Read back area containing data
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	data = InterpretDownloadedArea(response[0])

	countNodes = 0
	for el in data["way"][wayId]:
		if el.tag == "nd": countNodes += 1
	if countNodes != 3:
		return (0,"Error: way has incorrect number of child nodes")

	wayReadback = data["way"][wayId]
	if not CheckWayHasChildNodes(wayReadback, [nodeId1, nodeId2, nodeId3]):
		return (0,"Error way has incorrect child nodes")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]
	if save: open("verify.html", "wt").write(response[0])

	#*********** Delete way and nodes *********************

	if verbose>=1: print "Delete way", wayId
	deleteWay = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<delete>\n"+\
	"  <way id='"+str(wayId)+"' version='1' changeset='"+str(cid)+"'/>\n"+\
	"</delete>\n"+\
	"</osmChange>\n"

	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteWay,userpass)
	if verbose>=2: print response
	if save: open("del.html", "wt").write(response[0])
	diff = InterpretUploadResponse(response[0])
	
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting way")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]
	if save: open("verify.html", "wt").write(response[0])

	#Do internal checks the way has gone
	urlStr = conf.baseurl+"/0.6/way/{0}?bbox={1}".format(wayId, ",".join(map(str, bbox)))
	response = Get(urlStr)
	if save: open("check.html", "wt").write(response[0])

	#Check the way really has gone
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	data = InterpretDownloadedArea(response[0])
	if wayId in data["way"]:
		return (0,"Error way was not deleted")

	#Delete the remaining nodes
	ret, msg = DeleteSingleNode(nodeId1, cid, userpass, lat[2], lon[2], save, verbose)
	if not ret: return ret, msg
	ret, msg = DeleteSingleNode(nodeId2, cid, userpass, lat[1], lon[1], save, verbose)
	if not ret: return ret, msg
	ret, msg = DeleteSingleNode(nodeId3, cid, userpass, lat[3], lon[3], save, verbose)
	if not ret: return ret, msg

	#Close changeset
	if verbose>=1: print "Close changeset"
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	#Check nodes and way really have gone
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	data = InterpretDownloadedArea(response[0])
	if nodeId1 in data["node"] or nodeId2 in data["node"] or nodeId3 in data["node"]:
		return (0,"Error node(s) were not deleted")
	if wayId in data["way"]:
		return (0,"Error way was not deleted")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]


	#************ Area operations *******************

	tagGroupsToTest = [{"natural": "water"}, {"highway": "primary"}, {}]
	for tagGroupToTest in tagGroupsToTest:

		if verbose>=1: print "Open changeset"
		#Create a changeset
		createChangeset = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
		"<osm version='0.6' generator='JOSM'>\n" +\
		"  <changeset  id='0' open='false'>\n" +\
		"    <tag k='comment' v='python test function' />\n" +\
		"    <tag k='created_by' v='JOSM/1.5 (3592 en_GB)' />\n" +\
		"  </changeset>\n" +\
		"</osm>\n"

		response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
		if verbose>=2: print response
		cid = int(response[0])
		if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changeset")

		lat = [51.22203966503958, 51.219443198163034, 51.22001505165771]
		lon = [0.41224712359411547, 0.413727688103378, 0.4109146155357791]

		if verbose>=1: print "Create an initial node"
		#Create a way between two nodes
		create = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
		"<osmChange version='0.6' generator='JOSM'>\n" +\
		"<create version='0.6' generator='JOSM'>\n" +\
		"  <node id='-289' changeset='{0}' lat='{1}' lon='{2}' />\n".format(cid, lat[0], lon[0]) +\
		"</create>\n" +\
		"</osmChange>\n"
		response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",create,userpass)
		if verbose>=2: print response
		if save: open("add.html", "wt").write(response[0])
		if log is not None: 
			log.write(response[1])
			log.write(response[0])
		if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating node")
	
		diff = InterpretUploadResponse(response[0])
		nodeId1 = int(diff["node"][-289]["new_id"])

		if verbose>=1: print "Create an area between three nodes", tagGroupToTest
		#Create a way between two nodes
		create = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
		"<osmChange version='0.6' generator='JOSM'>\n" +\
		"<create version='0.6' generator='JOSM'>\n" +\
		"  <node id='-2008' changeset='{0}' lat='{1}' lon='{2}' />\n".format(cid, lat[1], lon[1])+\
		"  <node id='-356' changeset='{0}' lat='{1}' lon='{2}' />\n".format(cid, lat[2], lon[2])+\
		"  <way id='-2010' changeset='"+str(cid)+"'>\n"+\
		"    <nd ref='{0}' />\n".format(nodeId1)+\
		"    <nd ref='-2008' />\n"+\
		"    <nd ref='-356' />\n"+\
		"    <nd ref='{0}' />\n".format(nodeId1)
		for key in tagGroupToTest:
			create += "    <tag k='{0}' v='{1}' />\n".format(quoteattr(key), quoteattr(tagGroupToTest[key]))
		create += "  </way>\n"+\
		"</create>\n" +\
		"</osmChange>\n"
		response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",create,userpass)
		if verbose>=2: print response
		if save: open("add.html", "wt").write(response[0])
		if log is not None: 
			log.write(response[1])
			log.write(response[0])
		if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating area")
	
		diff = InterpretUploadResponse(response[0])
		nodeId2 = int(diff["node"][-2008]["new_id"])
		nodeId3 = int(diff["node"][-356]["new_id"])
		wayId = int(diff["way"][-2010]["new_id"])

		if verbose>=1: print "Close changeset"
		#Close the changeset
		response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
		if verbose>=2: print response
		if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

		#Read back single way object
		bbox = [min(lon), min(lat), max(lon), max(lat)]
		response = Get(conf.baseurl+"/0.6/way/{0}?bbox={1}".format(wayId, ",".join(map(str, bbox))))
		if save: open("add.html", "wt").write(response[0])

		#Read back area containing data
		response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
		if verbose>=2: print response
		if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
		data = InterpretDownloadedArea(response[0])
		node1Readback = data["node"][nodeId1]
		if not CheckNodePosition(node1Readback, lat[0], lon[0]):
			return (0,"Error node has bad position")
		node2Readback = data["node"][nodeId2]
		if not CheckNodePosition(node2Readback, lat[1], lon[1]):
			return (0,"Error node has bad position")
		node3Readback = data["node"][nodeId3]
		if not CheckNodePosition(node3Readback, lat[2], lon[2]):
			return (0,"Error node has bad position")
		wayReadback = data["way"][wayId]
		if not CheckWayHasChildNodes(wayReadback, [nodeId1, nodeId2, nodeId3]):
			return (0,"Error way has incorrect child nodes")

		countNodes = 0
		for el in data["way"][wayId]:
			if el.tag == "nd": countNodes += 1
		if countNodes != 4:
			return (0,"Error: way has incorrect number of child nodes")

		#Verify cache in this area
		bbox = [min(lon), min(lat), max(lon), max(lat)]
		response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
		if len(response[0]) > 0: print response[0]

		#Verify underlying database integrity in this area
		bbox = [min(lon), min(lat), max(lon), max(lat)]
		response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
		if len(response[0]) > 0: print response[0]
		if save: open("verify.html", "wt").write(response[0])


	#****** Relation operations *************

	if verbose>=1: print "Open changeset"
	#Create a changeset
	createChangeset = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	"<osm version='0.6' generator='JOSM'>\n" +\
	"  <changeset  id='0' open='false'>\n" +\
	"    <tag k='comment' v='python test function' />\n" +\
	"    <tag k='created_by' v='JOSM/1.5 (3592 en_GB)' />\n" +\
	"  </changeset>\n" +\
	"</osm>\n"

	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changeset")

	lat = [51.22203966503958, 51.219443198163034, 51.22001505165771]
	lon = [0.41224712359411547, 0.413727688103378, 0.4109146155357791]

	if verbose>=1: print "Create an area using relations"
	#Create a way between two nodes
	tagGroupToTest = {"natural": "water", "type": "multipolygon"}
	create = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	"<osmChange version='0.6' generator='JOSM'>\n" +\
	"<create>\n"+\
	"  <node id='-359' changeset='{0}' lat='51.21420467163' lon='-0.1701214362' />\n".format(cid)+\
	"  <node id='-357' changeset='{0}' lat='51.21664687637' lon='-0.18072625879' />\n".format(cid)+\
	"  <node id='-371' changeset='{0}' lat='51.21669571914' lon='-0.17307116972' />\n".format(cid)+\
	"  <node id='-370' changeset='{0}' lat='51.21840518357' lon='-0.17010805752' />\n".format(cid)+\
	"  <node id='-373' changeset='{0}' lat='51.21879590938' lon='-0.17517653891' />\n".format(cid)+\
	"  <node id='-367' changeset='{0}' lat='51.21962619072' lon='-0.1696401977' />\n".format(cid)+\
	"  <node id='-361' changeset='{0}' lat='51.22026110165' lon='-0.16357139872' />\n".format(cid)+\
	"  <node id='-365' changeset='{0}' lat='51.22162857236' lon='-0.17338307627' />\n".format(cid)+\
	"  <node id='-364' changeset='{0}' lat='51.22319134628' lon='-0.17096580053' />\n".format(cid)+\
	"  <node id='-356' changeset='{0}' lat='51.22680505777' lon='-0.17230478203' />\n".format(cid)+\
	"  <way id='-366' changeset='{0}'>\n".format(cid)+\
	"	<nd ref='-364' />\n"+\
	"	<nd ref='-365' />\n"+\
	"	<nd ref='-367' />\n"+\
	"	<nd ref='-364' />\n"+\
	"  </way>\n"+\
	"  <way id='-372' changeset='{0}'>\n".format(cid)+\
	"	<nd ref='-370' />\n"+\
	"	<nd ref='-371' />\n"+\
	"	<nd ref='-373' />\n"+\
	"	<nd ref='-370' />\n"+\
	"  </way>\n"+\
	"  <way id='-358' changeset='{0}'>\n".format(cid)+\
	"	<nd ref='-356' />\n"+\
	"	<nd ref='-357' />\n"+\
	"	<nd ref='-359' />\n"+\
	"	<nd ref='-361' />\n"+\
	"	<nd ref='-356' />\n"+\
	"  </way>\n"+\
	"  <relation id='-435' changeset='{0}'>\n".format(cid)+\
	"	<member type='way' ref='-366' role='outer' />\n"+\
	"	<member type='way' ref='-372' role='inner' />\n"+\
	"	<member type='way' ref='-358' role='inner' />\n"
	for key in tagGroupToTest:
		create += "    <tag k='{0}' v='{1}' />\n".format(quoteattr(key), quoteattr(tagGroupToTest[key]))
	create += "  </relation>\n"+\
	"</create>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload?debug=1",create,userpass)
	if verbose>=2: print response
	if save: open("add.html", "wt").write(response[0])
	if log is not None: 
		log.write(response[1])
		log.write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating area")

	diff = InterpretUploadResponse(response[0])
	print diff["relation"]
	wayId1 = int(diff["way"][-366]["new_id"])
	wayId2 = int(diff["way"][-372]["new_id"])
	wayId3 = int(diff["way"][-358]["new_id"])
	relId = int(diff["relation"][-435]["new_id"])

	if verbose>=1: print "Close changeset"
	#Close the changeset
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	#Verify cache in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifycache?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]

	#Verify underlying database integrity in this area
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/verifydb?bbox={0}".format(",".join(map(str, bbox))))
	if len(response[0]) > 0: print response[0]
	if save: open("verify.html", "wt").write(response[0])

	return (1,"OK")

def ReadDeletedNode(nodeId,verbose=0):
	#Attempt to read deleted node
	response = Get(conf.baseurl+"/0.6/node/"+str(nodeId))
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 410 Gone": 
		return (0,"Error deleted node had wrong header code")
	if response[0] != "":
		return (0,"Error reading deleted node had wrong message")

	return (1,"OK")


if __name__ == "__main__":

	username = conf.GetUsername()
	password = conf.GetPassword()
	userpass = username+":"+password

	print TestMultiObjectEditing(userpass,1,1)
	#print ReadDeletedNode(981182860,1)


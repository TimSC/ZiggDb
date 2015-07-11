import sys, conf
sys.path.append( "." )
from urlutil import *
import xml.etree.ElementTree as ET

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

def CheckWayHasChildNodes(wayXml, nodeIds):
	tmp = set()
	for el in wayXml:
		if el.tag != "nd": continue
		tmp.add(int(el.attrib["ref"]))
	for nid in nodeIds:
		if int(nid) not in tmp:
			return False
	return True

def TestMultiObjectEditing(userpass, verbose=0, save=False):

	log = open("log.txt", "wt")

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

	#Read back area containing node
	bbox = [min(lon), min(lat), max(lon), max(lat)]
	response = Get(conf.baseurl+"/0.6/map?bbox={0}".format(",".join(map(str, bbox))))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back area")
	data = InterpretDownloadedArea(response[0])
	node1Readback = data["node"][nodeId1]
	node2Readback = data["node"][nodeId2]
	wayReadback = data["way"][wayId]
	if not CheckWayHasChildNodes(wayReadback, [nodeId1, nodeId2]):
		return (0,"Error way has incorrect child nodes")

	if verbose>=1: print "Open changeset"
	#Open another changeset
	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changset")

	if verbose>=1: print "Modify a node with id:", nodeId1
	#Modify test node
	lat = 51.25
	lon = -0.60
	modifyNode = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<modify>\n"+\
	"  <node id='"+str(nodeId1)+"' version='1' changeset='"+str(cid)+"' lat='"+str(lat)+"' lon='"+str(lon)+"' />\n"+\
	"</modify>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",modifyNode,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error modifying node")
	diff = InterpretUploadResponse(response[0])

	if verbose>=1: print "Close changeset"
	#Close changeset
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	#Open changeset
	if verbose>=1: print "Open changeset"
	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose>=2: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changset")

	if verbose>=1: print "Delete way"
	deleteWay = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<delete>\n"+\
	"  <way id='"+str(wayId)+"' version='1' changeset='"+str(cid)+"'/>\n"+\
	"</delete>\n"+\
	"</osmChange>\n"

	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteWay,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	diff = InterpretUploadResponse(response[0])
	print response[0]
	
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting way")

	if verbose>=1: print "Delete node"
	deleteNode = '<osmChange version="0.6" generator="JOSM">' +\
	"<delete>\n" +\
	"  <node id='"+str(nodeId1)+"' version='2' "+\
	"changeset='"+str(cid)+"' lat='"+str(lat)+"'  lon='"+str(lon)+"' />\n"+\
	"</delete>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteNode,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")
	diff = InterpretUploadResponse(response[0])

	if verbose>=1: print "Delete another node"
	deleteNode = '<osmChange version="0.6" generator="JOSM">' +\
	"<delete>\n" +\
	"  <node id='"+str(nodeId2)+"' version='1' "+\
	"changeset='"+str(cid)+"' lat='"+str(lat)+"'  lon='"+str(lon)+"' />\n"+\
	"</delete>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteNode,userpass)
	if verbose>=2: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")
	diff = InterpretUploadResponse(response[0])

	#Delete a non-existant node
	#nonExistId = 999999999999999
	#deleteNode = '<osmChange version="0.6" generator="JOSM">' +\
	#"<delete>\n" +\
	#"  <node id='"+str(nonExistId)+"' version='1' "+\
	#"changeset='"+str(cid)+"' lat='"+str(lat)+"'  lon='"+str(lon)+"' />\n"+\
	#"</delete>\n"+\
	#"</osmChange>\n"
	#response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteNode,userpass)
	#if verbose: print response
	#if save: open("mod.html", "wt").write(response[0])
	#if HeaderResponseCode(response[1]) != "HTTP/1.1 409 Conflict": return (0,"Error deleting node")
	#diff = InterpretUploadResponse(response[0])

	#Close changeset
	if verbose>=1: print "Close changeset"
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	return (1,"OK")

	#Attempt to read deleted node
	response = Get(conf.baseurl+"/0.6/node/"+str(nodeId))
	if verbose>=2: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 410 Gone": 
		return (0,"Error deleted node had wrong header code")
	if response[0] != "":#"The node with the id "+str(nodeId)+" has already been deleted":
		return (0,"Error reading deleted node had wrong message")

	#Check nodes have been deleted OK
	ret = ReadDeletedNode(nodeId)
	if ret[0] == 0: return ret
	ret = ReadDeletedNode(nodeId2)
	if ret[0] == 0: return ret

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


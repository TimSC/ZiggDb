import sys, conf
sys.path.append( "." )
from urlutil import *
import xml.etree.ElementTree as ET
from sqlitedict import SqliteDict

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
	lat = []
	lon = []

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
	nodeId1 = 318

	if verbose>=1: print "Modify (by translation) a node with id:", nodeId1
	#Modify test node
	lat.append(51.20199306333155)
	lon.append(-0.40432534402173914)
	modifyNode = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<modify>\n"+\
	"  <node id='"+str(nodeId1)+"' version='1' changeset='"+str(cid)+"' lat='"+str(lat[0])+"' lon='"+str(lon[0])+"' />\n"+\
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

if __name__ == "__main__":

	username = conf.GetUsername()
	password = conf.GetPassword()
	userpass = username+":"+password

	print TestMultiObjectEditing(userpass,1,1)
	#print ReadDeletedNode(981182860,1)


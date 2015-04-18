import sys, conf
sys.path.append( "." )
from urlutil import *
import xml.etree.ElementTree as ET

def InterpretUploadResponse(response):
	root = ET.fromstring(response)
	diff = {"node": {}, "way": {}, "relation": {}}
	for el in root:
		val = {}
		for k in el.attrib:
			val[k] = int(el.attrib[k])
		diff[el.tag][int(el.attrib["old_id"])] = val
	return diff

def TestMultiObjectEditing(userpass, verbose=0, save=False):

	#Create a changeset
	createChangeset = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	"<osm version='0.6' generator='JOSM'>\n" +\
	"  <changeset  id='0' open='false'>\n" +\
	"    <tag k='comment' v='python test function' />\n" +\
	"    <tag k='created_by' v='JOSM/1.5 (3592 en_GB)' />\n" +\
	"  </changeset>\n" +\
	"</osm>\n"

	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changeset")

	lat = 51.25022331526812
	lon = -0.6042092878597837

	#Create a way between two nodes
	create = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	"<osmChange version='0.6' generator='JOSM'>\n" +\
	"<create version='0.6' generator='JOSM'>\n" +\
	"  <node id='-289' changeset='"+str(cid)+"' lat='"+str(lat)+"' lon='"+str(lon)+"' />\n" +\
	"  <node id='-2008' changeset='"+str(cid)+"' lat='51.2419166618214' lon='-0.5910182209303836' />\n"+\
	"  <way id='-2010' changeset='"+str(cid)+"'>\n"+\
	"    <nd ref='-289' />\n"+\
	"    <nd ref='-2008' />\n"+\
	"  </way>\n"+\
	"</create>\n" +\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",create,userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating node")
	#wayId = int(response[0])
	print response[0]
	
	diff = InterpretUploadResponse(response[0])
	nodeId1 = diff["node"][-289]["new_id"]
	nodeId2 = diff["node"][-2008]["new_id"]

	#Close the changeset
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	if 0:
		#Read back node
		response = Get(conf.baseurl+"/0.6/node/"+str(nodeId1))
		if verbose: print response
		if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error reading back node")

	#Open another changeset
	response = Put(conf.baseurl+"/0.6/changeset/create",createChangeset,userpass)
	if verbose: print response
	cid = int(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error creating changset")

	#Modify test node
	lat = 51.25
	lon = -0.60
	modifyNode = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<modify>\n"+\
	"  <node id='"+str(nodeId1)+"' version='1' changeset='"+str(cid)+"' lat='"+str(lat)+"' lon='"+str(lon)+"' />\n"+\
	"</modify>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",modifyNode,userpass)
	if verbose: print response
	if save: open("mod.html", "wt").write(response[0])
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error modifying node")

	#Close changeset
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	return (1,"OK")

	#Open changeset

	#Delete test node
	#It seems that pycurl doesn't allow the delete method to upload content. Use the multi object API insted.
	#deleteNode = "<?xml version='1.0' encoding='UTF-8'?>\n" +\
	#"<osm version='0.6' generator='JOSM'>\n" +\
	#"  <node id='"+str(nodeId1)+"' changeset='"+str(cid)+"' version='2' />\n" +\
	#"</osm>\n"
	#response = Delete(conf.baseurl+"/0.6/node/"+str(nodeId1),deleteNode,userpass)
	#if verbose: print response
	#if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")

	deleteWay = '<osmChange version="0.6" generator="JOSM">'+"\n"+\
	"<delete>\n"+\
	"  <way id='"+str(wayId)+"' version='1' changeset='"+str(cid)+"'/>\n"+\
	"</delete>\n"+\
	"</osmChange>\n"

	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteWay,userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")

	deleteNode = '<osmChange version="0.6" generator="JOSM">' +\
	"<delete>\n" +\
	"  <node id='"+str(nodeId1)+"' version='2' "+\
	"changeset='"+str(cid)+"' lat='"+str(lat)+"'  lon='"+str(lon)+"' />\n"+\
	"</delete>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteNode,userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")

	deleteNode = '<osmChange version="0.6" generator="JOSM">' +\
	"<delete>\n" +\
	"  <node id='"+str(nodeId2)+"' version='1' "+\
	"changeset='"+str(cid)+"' lat='"+str(lat)+"'  lon='"+str(lon)+"' />\n"+\
	"</delete>\n"+\
	"</osmChange>\n"
	response = Post(conf.baseurl+"/0.6/changeset/"+str(cid)+"/upload",deleteNode,userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error deleting node")

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
	#if HeaderResponseCode(response[1]) != "HTTP/1.1 409 Conflict": return (0,"Error deleting node")

	#Close changeset
	response = Put(conf.baseurl+"/0.6/changeset/"+str(cid)+"/close","",userpass)
	if verbose: print response
	if HeaderResponseCode(response[1]) != "HTTP/1.1 200 OK": return (0,"Error closing changeset")

	return (1,"OK")

	#Attempt to read deleted node
	response = Get(conf.baseurl+"/0.6/node/"+str(nodeId))
	if verbose: print response
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


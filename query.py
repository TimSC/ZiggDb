

import zigg
import bz2, cPickle, uuid

if __name__ == "__main__":
	ziggDb = zigg.ZiggDb()

	ziggDb.GenerateTestData()

	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])

	#==Node operations==
	#Basic concept: nodes may only be changed inside the active area

	#Add point within active area (allowed)
	userInfo = {}
	newNode = [[[[[51.129, -0.272, None]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	idChanges = ziggDb.SetArea(area, userInfo)
	nodeId = idChanges["nodes"].values()[0]
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	diffs = zigg.CompareAreas(area, area2)
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding node"
		print diffs
	area = area2

	#Move point within active area (allowed)
	area["nodes"][nodeId] = [[[[[51.129, -0.272, None]], None]], {'name': 'another place'}]
	idChanges = ziggDb.SetArea(area, userInfo)
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	diffs = zigg.CompareAreas(area, area2)
	if len(diffs) > 0:
		print "Unexpected differences discovered when moving node"
		print diffs
	area = area2

	#Add point outside active area (not allowed)
	userInfo = {}
	newNode = [[[[[51.11, -0.272, None]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		print "Unexpected lack of expection when adding node outside active area"

	#Move point in, from or into outside active area (not allowed)
	area["nodes"][nodeId] = [[[[[51.11, -0.272, None]], None]], {'name': 'another place'}]
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except:
		ex = True
	if not ex:
		print "Unexpected lack of expection when moving node outside active area"

	#Delete point outside active area (not allowed)
	#In fact there should never been single nodes outside the active area

	#Delete point within active area (allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	del area["nodes"][nodeId]
	idChanges = ziggDb.SetArea(area, userInfo)
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	diffs = zigg.CompareAreas(area, area2)
	if len(diffs) > 0:
		print "Unexpected differences discovered when moving node"
		print diffs
	area = area2

	#Create a point with a client specified UUID (not allowed)
	userInfo = {}
	newNode = [[[[[51.129, -0.272, None]], None]], {'name': 'another place'}]
	area["nodes"][uuid.uuid4().bytes] = newNode
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except:
		ex = True
	if not ex:
		print "Unexpected lack of expection when moving node outside active area"

	#Uploading node with multiple locations (not allowed)


	#==Way operations==
	#Basic concept: The shapes of ways outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated

	#Create way full within active area (allowed)

	#Create way partly within active area (allowed)

	#Create way partly outside active area (not allowed)

	#Modify tags of way within or partly within active area (allowed)

	#Reorder nodes in way that is partially outside active area (allowed)
	
	#Add or remove nodes from a way that are outside the active area (not allowed)

	#Delete way within active area (allowed)	

	#Delete way partly within or outside active area (not allowed)

	#==Area operations==
	#Basic concept: The shapes of areas outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated
	



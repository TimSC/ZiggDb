

import zigg
import bz2, cPickle, uuid, slippy

if __name__ == "__main__":
	testPass = 0
	testFail = 0
	testWarning = 0

	ziggDb = zigg.ZiggDb()

	ziggDb.GenerateTestData()

	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])

	#==Node operations==
	#Basic concept: nodes may only be changed inside the active area

	#Add point within active area (allowed)
	userInfo = {}
	newNode = [[[[[51.129, -0.272, -1]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	#print area["nodes"]
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)
	nodeId = idChanges["nodes"].values()[0]
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	nodeData = area2["nodes"][nodeId]
	#print area2["nodes"]
	diffs = zigg.CompareAreas(area, area2)
	ok = True
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding node"
		print diffs
		ok = False
	
	#Check node ID has been updated
	nodeId2 = nodeData[0][0][0][0][2]
	if nodeId != nodeId2:
		print "Incorrect node ID in data when adding node"
		ok = False

	if ok:
		testPass += 1
	else:
		testFail += 1

	area = area2

	#Move point within active area (allowed)
	area["nodes"][nodeId] = [[[[[51.129, -0.272, nodeId]], None]], {'name': 'another place'}]
	idChanges = ziggDb.SetArea(area, userInfo)
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	diffs = zigg.CompareAreas(area, area2)
	if len(diffs) > 0:
		print "Unexpected differences discovered when moving node"
		print diffs
		testFail += 1
	else:
		testPass += 1
	area = area2

	#Change node tags within active area (allowed)
	area["nodes"][nodeId] = [[[[[51.129, -0.272, nodeId]], None]], {'name': 'test tag'}]

	idChanges = ziggDb.SetArea(area, userInfo)
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	diffs = zigg.CompareAreas(area, area2)
	if len(diffs) > 0:
		print "Unexpected differences discovered when changing tags of node"
		print diffs
		testFail += 1
	else:
		testPass += 1
	area = area2

	#Add point outside active area (not allowed)
	userInfo = {}
	newNode = [[[[[51.11, -0.272, -1]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		print "Unexpected lack of exception when adding node outside active area"
		testFail += 1
	else:
		testPass += 1

	#Move point in, from or into outside active area (not allowed)
	area["nodes"][nodeId] = [[[[[51.11, -0.272, None]], None]], {'name': 'another place'}]
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except:
		ex = True
	if not ex:
		print "Unexpected lack of exception when moving node outside active area"
		testFail += 1
	else:
		testPass += 1

	#Delete point outside active area (not allowed)
	#In fact there should never been single nodes outside the active area

	#Create a point with a client specified UUID (not allowed)
	userInfo = {}
	newNode = [[[[[51.129, -0.272, None]], None]], {'name': 'another place'}]
	area["nodes"][uuid.uuid4().bytes] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when moving node outside active area"
	else:
		testPass += 1

	#Upload node with non-matching UUIDs (not allowed)
	newNode = [[[[[51.129, -0.272, -2]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when adding node with wrong ID"
	else:
		testPass += 1
	
	#Modify node by changing its UUID (not allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	nodeId1 = area["nodes"].keys()[0]
	nodeId2 = area["nodes"].keys()[1]
	area["nodes"][nodeId1] = [[[[[51.129, -0.272, nodeId2]], None]], {'name': 'another place'}]
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True		
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when modifying node with wrong ID"
	else:
		testPass += 1

	#Delete point within active area (allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	del area["nodes"][nodeId]
	idChanges = ziggDb.SetArea(area, userInfo)
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	diffs = zigg.CompareAreas(area, area2)
	if len(diffs) > 0:
		print "Unexpected differences discovered when moving node"
		print diffs
		testFail += 1
	else:
		testPass += 1
	area = area2

	#Uploading node with multiple locations (not allowed)
	newNode = [[[[[51.129, -0.272, -1], [51.1291, -0.2721, -1]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when adding node with multiple locations"
	else:
		testPass += 1

	#Upload node with inner polygon (not allowed)
	newNode = [[[[[51.129, -0.272, -1]], []]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when adding node with inner polygon"
	else:
		testPass += 1

	#Upload node with invalid lat/lon (not allowed)
	newNode = [[[[[-90.1, -0.272, -1]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when adding node with invalid position"
	else:
		testPass += 1

	#Upload a node with invalid tag info (not allowed)
	newNode = [[[[[51.129, -0.272, -1]], None]], ['name', 'another place']]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError as err:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when adding node with invalid tags"
	else:
		testPass += 1

	#Upload two nodes with the same negative id (not allowed)
	#This is actually impossible because a dict can only have one value per key

	#==Way operations==
	#Basic concept: The shapes of ways outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated

	#Create way full within active area (allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	userInfo = {}
	newWay = [[[[[51.128, -0.271, -1], [51.127, -0.269, -2]], None]], {'name': 'old road'}]
	area["ways"][-1] = newWay
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)
	wayId = idChanges["ways"].values()[0]
	
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	wayData = area2["ways"][wayId]
	#print area2["nodes"]
	diffs = zigg.CompareAreas(area, area2)
	ok = True
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding node"
		print diffs
		ok = False
	area = area2

	#Check ids of nodes within new way
	wayShape, wayTags = wayData
	newWayNodeIds = []
	if len(wayShape) == 1:
		outer, inners = wayShape[0]
		if len(outer) != 2:
			print "Way has unexpected length"
			ok = False			

		for pt in outer:
			if isinstance(pt[2], int):
				print "Nodes in way have not been renumbered"
				ok = False
			newWayNodeIds.append(pt[2])

		if inners is not None:
			print "Ways should have no inners information"
			ok = False
	else:
		print "Way shape has wrong length"
		ok = False

	if ok:
		testPass += 1
	else:
		testFail += 1

	#Modify tags of way within or partly within active area (allowed)
	wayData = area["ways"][wayId]
	wayData[1]["name"] = "new named road"
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)

	bbox = [-0.3, 51.12, -0.19, 51.17]
	area2 = ziggDb.GetArea(bbox)
	#wayData = area2["ways"][wayId]
	#print area2["nodes"]
	diffs = zigg.CompareAreas(area, area2)
	ok = True
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding node"
		print diffs
		ok = False
	if ok:
		testPass += 1
	else:
		testFail += 1
	area = area2

	#Reorder nodes in way that is partially outside active area (allowed)
	waysPartlyInside = zigg.FindPartlyOutside(area["ways"], bbox)
	testWayUuid = waysPartlyInside.keys()[0]
	testWayData = area["ways"][testWayUuid]
	wayShape, wayTags = testWayData
	wayPoly = wayShape[0]
	outer, inners = wayPoly
	wayPoly = outer[::-1]
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)

	area2 = ziggDb.GetArea(bbox)
	diffs = zigg.CompareAreas(area, area2)
	ok = True
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding node"
		print diffs
		ok = False
	if ok:
		testPass += 1
	else:
		testFail += 1

	#Create way partly or fully outside active area (not allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	userInfo = {}
	newWay = [[[[[61.128, -0.271, -1], [61.127, -0.269, -2]], None]], {'name': 'far away road'}]
	area["ways"][-1] = newWay
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when adding way outside active area"
	else:
		testPass += 1
	
	#Create a way across internal tile boundary (allowed)
	#print slippy.num2deg(2044, 1369, 12)


	#Modify way tags across tile boundary (allowed)

	#Move point inside active area across internal tile boundary (allowed)

	#Add point to way that crosses internal tile boundary (allowed)

	#Move a node in a way outside the active area (silently ignored)

	
	#Add or remove nodes from a way that are outside the active area (not allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	waysPartlyInside = zigg.FindPartlyOutside(area["ways"], bbox)
	testWayUuid = waysPartlyInside.keys()[0]
	testWayData = area["ways"][testWayUuid]
	wayShape, wayTags = testWayData
	wayPoly = wayShape[0]

	print testWayUuid
	outer, inners = wayPoly
	print len(outer)

	insidePts = []
	for pt in outer:
		inside = zigg.CheckPointInRect(pt, bbox)
		if not inside: continue
		insidePts.append(pt)
	wayPoly[0] = insidePts

	print len(insidePts)

	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when removing outside node from way"
	else:
		testPass += 1

	#Delete way within active area (allowed)	

	#Delete way partly within or outside active area (not allowed)

	#Upload objects with contraditory positions for a shared UUID node (allowed, silently fixed)

	#==Area operations==
	#Basic concept: The shapes of areas outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated
	
	print "Tests passed", testPass
	print "Tests failed", testFail


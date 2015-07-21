

import zigg
import bz2, cPickle, uuid, slippy, config, os

if __name__ == "__main__":
	testPass = 0
	testFail = 0
	testWarning = 0

	ziggDb = zigg.ZiggDb(config.repos, os.path.dirname(__file__))

	#Verify data integrity
	result = ziggDb.Verify([-0.3, 51.12, -0.19, 51.17])
	print result

	#Generate test data
	ziggDb.GenerateTestData()

	#Verify data integrity
	result = ziggDb.Verify([-0.3, 51.12, -0.19, 51.17])
	print result

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

	#Verify data integrity
	result = ziggDb.Verify([-0.3, 51.12, -0.19, 51.17])
	print result
	
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
	newNode = [[[[[51.11, -0.272, -1]], None]], {'name': 'far away place'}]
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

	#Verify data integrity
	result = ziggDb.Verify([-0.3, 51.12, -0.19, 51.17])
	print result
		
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
		print "Unexpected differences discovered when adding way"
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
	tl = slippy.num2deg(2044, 1369, 12)
	mid = slippy.num2deg(2045, 1369, 12)
	br = slippy.num2deg(2046, 1370, 12)
	area = ziggDb.GetArea([tl[1]+0.0001, br[0]+0.0001, br[1]-0.0001, tl[0]-0.0001])
	pt1 = (zigg.Interp(tl[0], br[0], 0.5), zigg.Interp(tl[1], br[1], 0.25))
	pt2 = (zigg.Interp(tl[0], br[0], 0.5), zigg.Interp(tl[1], br[1], 0.75))

	area["ways"][-1] = [[[[[pt1[0], pt1[1], -1], [pt2[0], pt2[1], -2]], None]], {'name': 'spanning road'}]
	idChanges = ziggDb.SetArea(area, userInfo)
	newWayId = idChanges["ways"].values()[0]
	ok = True
	area1 = ziggDb.GetArea([tl[1]+0.0001, br[0]+0.0001, mid[1]-0.0001, tl[0]-0.0001])
	if newWayId not in area1["ways"]:
		print "Expected way missing in tile"
		ok = False
	area2 = ziggDb.GetArea([mid[1]+0.0001, br[0]+0.0001, br[1]-0.0001, mid[0]-0.0001])
	if newWayId not in area2["ways"]:
		print "Expected way missing in tile"
		ok = False

	if ok:
		testPass += 1
	else:
		testFail += 1

	#Modify way tags across tile boundary (allowed)
	area1 = ziggDb.GetArea([tl[1]+0.0001, br[0]+0.0001, mid[1]-0.0001, tl[0]-0.0001])
	area1["ways"][newWayId][1] = {'name': 'updated name'}
	idChanges = ziggDb.SetArea(area1, userInfo)
	ok = True
	
	area1 = ziggDb.GetArea([tl[1]+0.0001, br[0]+0.0001, mid[1]-0.0001, tl[0]-0.0001])
	if area1["ways"][newWayId][1]["name"] != "updated name":
		print "Tag did not update as expected (primary tile)"
		ok = False

	area2 = ziggDb.GetArea([mid[1]+0.0001, br[0]+0.0001, br[1]-0.0001, mid[0]-0.0001])
	if area2["ways"][newWayId][1]["name"] != "updated name":
		print "Tag did not update as expected (related tile)"
		ok = False
	
	if ok:
		testPass += 1
	else:
		testFail += 1

	#Move point inside active area across internal tile boundary (allowed)
	area = ziggDb.GetArea([tl[1]+0.0001, br[0]+0.0001, br[1]-0.0001, tl[0]-0.0001])
	pt3 = (zigg.Interp(tl[0], br[0], 0.5), zigg.Interp(tl[1], br[1], 0.80))

	wayToMod = area["ways"][newWayId]
	objShapes, objTags = wayToMod
	objShape = objShapes[0]
	outer, inners = objShape

	area["ways"][newWayId] = [[[[[pt2[0], pt2[1], outer[0][2]], [pt3[0], pt3[1], outer[1][2]]], None]], 
		{'name': 'spanning road'}]

	idChanges = ziggDb.SetArea(area, userInfo)

	ok = True
	area1 = ziggDb.GetArea([tl[1]+0.0001, br[0]+0.0001, mid[1]-0.0001, tl[0]-0.0001])
	if newWayId not in area1["ways"]:
		print "Way unexpectedly missing in tile"
		ok = False

	area2 = ziggDb.GetArea([mid[1]+0.0001, br[0]+0.0001, br[1]-0.0001, mid[0]-0.0001])
	if newWayId in area2["ways"]:
		print "Way unexpectedly present in tile"
		ok = False

	if ok:
		testPass += 1
	else:
		testFail += 1
	
	#Add point to way that crosses repo boundary (allowed)

	#Create a way across repo boundary (allowed)

	#Modify way tags across repo boundary (allowed)

	#Move point inside active area across repo boundary (allowed)

	#Add point to way that crosses repo boundary (allowed)



	#Move a node in a way outside the active area (silently ignored)
	bbox = [-0.3, 51.12, -0.19, 51.17]
	area = ziggDb.GetArea(bbox)
	waysPartlyInside = zigg.FindPartlyOutside(area["ways"], bbox)
	wayToModify = waysPartlyInside.keys()[0]
	
	wayObj = waysPartlyInside[wayToModify]
	wayShape, wayTags = wayObj
	wayPoly = wayShape[0]
	outer, inners = wayPoly
	nodeIndex = None
	for nodeIndex, pt in enumerate(outer):
		if zigg.CheckPointInRect(pt, bbox): continue
		break
	outer[nodeIndex][0] = 60.
	outer[nodeIndex][1] = -10.
	idChanges = ziggDb.SetArea(area, userInfo)

	area = ziggDb.GetArea(bbox)
	wayObj = area["ways"][wayToModify]
	wayShape, wayTags = wayObj
	wayPoly = wayShape[0]
	outer, inners = wayPoly
	if outer[nodeIndex][0] > 55. or outer[nodeIndex][0] < -5.:
		print "Node in way updated even though it is outside active area"
		testFail += 1
	else:
		testPass += 1
	
	#Add or remove nodes from a way that are outside the active area (not allowed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	waysPartlyInside = zigg.FindPartlyOutside(area["ways"], bbox)
	testWayUuid = waysPartlyInside.keys()[0]
	testWayData = area["ways"][testWayUuid]
	wayShape, wayTags = testWayData
	wayPoly = wayShape[0]

	outer, inners = wayPoly

	insidePts = []
	for pt in outer:
		inside = zigg.CheckPointInRect(pt, bbox)
		if not inside: continue
		insidePts.append(pt)
	wayPoly[0] = insidePts

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
	bbox = [-0.3, 51.12, -0.19, 51.17]
	area = ziggDb.GetArea(bbox)
	waysInside = zigg.FindEntirelyInside(area["ways"], bbox)
	wayToDel = waysInside.keys()[0]
	del area["ways"][wayToDel]
	idChanges = ziggDb.SetArea(area, userInfo)
	
	area = ziggDb.GetArea(bbox)
	if wayToDel in area["ways"]:
		print "Way still present after being deleted"
		testFail += 1
	else:
		testPass += 1

	#Delete way partly within or outside active area (not allowed)
	bbox = [-0.3, 51.12, -0.19, 51.17]
	area = ziggDb.GetArea(bbox)
	waysInside = zigg.FindPartlyOutside(area["ways"], bbox)
	wayToDel = waysInside.keys()[0]
	del area["ways"][wayToDel]
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when deleting way partly outside active area"
	else:
		testPass += 1
	
	#Upload new objects with contraditory positions for a shared UUID node (allowed, silently fixed)
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	userInfo = {}
	newWay = [[[[[51.128, -0.271, -1], [51.127, -0.269, -1]], None]], {'name': 'condtradictory positions'}]
	area["ways"][-1] = newWay
	idChanges = ziggDb.SetArea(area, userInfo, -1)
	zigg.ApplyIdChanges(area, idChanges)
	wayId = idChanges["ways"].values()[0]
	
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	wayData = area2["ways"][wayId]
	wayShape, wayTags = wayData
	wayPoly = wayShape[0]
	outer, inners = wayPoly
	if outer[0] != outer[1]:
		testFail += 1
		print "Points with IDs should have the same position"
	else:
		testPass += 1

	#==Area operations==
	#Basic concept: The shapes of areas outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated
	
	#Create an area in active area
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	userInfo = {}
	newArea = [[[[[51.128, -0.271, -1], [51.127, -0.269, -2], [51.1275, -0.272, -3]], []]], {'name': 'lake'}]
	area["areas"][-1] = newArea
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)
	areaId = idChanges["areas"].values()[0]
	
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	areaData = area2["areas"][areaId]
	#print area2["nodes"]
	diffs = zigg.CompareAreas(area, area2)
	ok = True
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding area"
		print diffs
		ok = False
	if ok:
		testPass += 1
	else:
		testFail += 1
	area = area2

	#Modify tag for an area in active area
	newArea = [[[[[51.128, -0.271, -1], [51.127, -0.269, -2], [51.1275, -0.272, -3]], []]], {'name': 'wood'}]
	area["areas"][areaId] = newArea
	idChanges = ziggDb.SetArea(area, userInfo)

	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	areaData = area2["areas"][areaId]
	objShape, objTags = areaData
	if objTags["name"] != "wood":
		print "Wrong tag after area modified"
		testFail += 1
	else:
		testPass += 1

	#Delete area in active area
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	del area["areas"][areaId]
	idChanges = ziggDb.SetArea(area, userInfo)

	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	if areaId in area2["areas"]:
		print "Failed to delete area"
		testFail += 1
	else:
		testPass += 1

	#Create area with inner way
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	userInfo = {}
	a, b = 51.0767134647, 1.186346014
	clat, clon = 51.15, -0.25

	newArea = [[[[[51.0768857186-a+clat, 1.1862078673-b+clon, -1], 
		[51.0766380201-a+clat, 1.1861000067-b+clon, -2], 
		[51.0765281911-a+clat, 1.1865016947-b+clon, -3], 
		[51.0767548592-a+clat, 1.1865872393-b+clon, -4]], 
		[[[51.0767852373-a+clat, 1.1862859733-b+clon, -5], 
		[51.0767385017-a+clat, 1.1864421853-b+clon, -6], 
		[51.0766637247-a+clat, 1.1862971313-b+clon, -7]]]]], {'name': 'doughnut'}]
	area["areas"][-1] = newArea
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)
	areaId = idChanges["areas"].values()[0]
	
	area2 = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	areaData = area2["areas"][areaId]
	diffs = zigg.CompareAreas(area, area2)
	ok = True
	if len(diffs) > 0:
		print "Unexpected differences discovered when adding area with inner hole"
		print diffs
		ok = False
	if ok:
		testPass += 1
	else:
		testFail += 1
	area = area2

	#==Version operations==
	#Attempt to upload data based on out of date
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])
	userInfo = {}
	newNode = [[[[[51.129, -0.272, -1]], None]], {'name': 'another place'}]
	area["nodes"][-1] = newNode
	#print area["nodes"]
	idChanges = ziggDb.SetArea(area, userInfo)
	zigg.ApplyIdChanges(area, idChanges)
	nodeId = idChanges["nodes"].values()[0]

	newNode = [[[[[51.1297, -0.2723, -1]], None]], {'name': 'alternate place'}]
	area["nodes"][-1] = newNode
	ex = False
	try:
		idChanges = ziggDb.SetArea(area, userInfo)
	except ValueError:
		ex = True
	if not ex:
		testFail += 1
		print "Unexpected lack of exception when uploading data with the wrong version number"
	else:
		testPass += 1

	#Verify data integrity
	result = ziggDb.Verify([-0.3, 51.12, -0.19, 51.17])
	print result

	print "Tests passed", testPass
	print "Tests failed", testFail


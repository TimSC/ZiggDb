import cPickle, uuid, slippy, os, copy

def CheckRectOverlap(rect1, rect2):
	#left,bottom,right,top

	if rect1[2] < rect2[0]: return 0
	if rect1[0] > rect2[2]: return 0
	if rect1[1] > rect2[3]: return 0
	if rect1[3] < rect2[1]: return 0
	return 1

def CheckPointInRect(pt, rect):
	#left,bottom,right,top

	if rect[0] > rect[2] or rect[1] > rect[3]:
		raise ValueError("Invalid rectangle")

	if pt[1] < rect[0] or pt[1] > rect[2]: return 2
	if pt[0] < rect[1] or pt[0] > rect[3]: return 3
	return 1

def Interp(a, b, frac):
	return a * frac + b * (1. - frac)

def FindPartlyOutside(objsDict, bbox):
	out = {}
	for objId in objsDict:
		objData = objsDict[objId]
		shapes = objData[0]
		tags = objData[1]
		found = False
		for shape in shapes:
			outer, inners = shape
		
			for pt in outer:
				if not CheckPointInRect(pt, bbox):
					found = True
					break
			if not found and inners is not None:
				for inner in inners:
					for pt in inners:
						if not CheckPointInRect(pt, bbox):
							found = True
							break
					if found:
						break
					
		if found != False:
			out[objId] = objData
	return out

def FindEntirelyInside(objsDict, bbox):
	out = {}
	for objId in objsDict:
		objData = objsDict[objId]
		shapes = objData[0]
		tags = objData[1]
		found = False
		for shape in shapes:
			outer, inners = shape
		
			for pt in outer:
				if not CheckPointInRect(pt, bbox):
					found = True
					break
			if not found and inners is not None:
				for inner in inners:
					for pt in inners:
						if not CheckPointInRect(pt, bbox):
							found = True
							break
					if found:
						break
					
		if found != True:
			out[objId] = objData
	return out

def Trim(objsDict, bbox, invert = False):
	out = {}
	for objId in objsDict:
		objData = objsDict[objId]
		shapes = objData[0]
		tags = objData[1]
		found = False
		for shape in shapes:
			outer, inners = shape
			
			for pt in outer:
				if CheckPointInRect(pt, bbox):
					found = True
					break
			if not found and inners is not None:
				for inner in inners:
					for pt in inners:
						if CheckPointInRect(pt, bbox):
							found = True
							break
					if found:
						break
						
		if found != invert:
			out[objId] = objData
	return out

def CompareAreaObjs(area1Objs, area2Objs, ty):
	diff = []
	for objId in area1Objs:
		if objId not in area2Objs:
			diff.append("{0} missing from area2".format(ty))

	for objId in area2Objs:
		if objId not in area1Objs:
			diff.append("{0} missing from area1".format(ty))
	
	for objId in area1Objs:
		if objId not in area2Objs: continue
		obj1 = area1Objs[objId]
		obj2 = area2Objs[objId]
		shapes1, tags1 = obj1
		shapes2, tags2 = obj2

		if tags1 != tags2:
			diff.append("{0} tag differences".format(ty))
		if shapes1 != shapes2:
			diff.append("{0} shape/location/member id differences".format(ty))
		#print tags1, tags2

	return diff

def CompareAreas(area1, area2):
	diffs = []
	diffs.extend(CompareAreaObjs(area1["nodes"], area2["nodes"], "node"))
	diffs.extend(CompareAreaObjs(area1["ways"], area2["ways"], "way"))
	diffs.extend(CompareAreaObjs(area1["areas"], area2["areas"], "area"))
	return diffs

def ApplyIdChanges(area, idChanges):

	#Change dict IDs
	for objType in idChanges:
		tyChanges = idChanges[objType]
		for ch in tyChanges:
			if ch not in area[objType]: continue
			area[objType][tyChanges[ch]] = area[objType][ch]
			del area[objType][ch]

	#Change member node IDs
	nodeChanges = idChanges["nodes"]
	for objType in area:
		if objType not in ["nodes", "ways", "areas"]: continue

		typeObjs = area[objType]
		for objId in typeObjs:
			objData = typeObjs[objId]
			
			#Update member UUIDs
			shapes, tags = objData
			for shape in shapes:
				outer, inners = shape
				for pt in outer:
					ptId = pt[2]
					if not isinstance(ptId, int):
						continue
					pt[2] = nodeChanges[ptId]

				if inners is None: continue
				for inner in inners:
					for pt in inner:
						ptId = pt[2]
						if not isinstance(ptId, int):
							continue
						pt[2] = nodeChanges[ptId]


# ****************** Main class **********************

class ZiggDb(object):
	
	def __init__(self, repos, basePath):
		self.repos = repos
		self.basePath = basePath

	def GenerateTestData(self):

		for repoName in self.repos:
			repoData = self.repos[repoName]
			repoZoom = repoData[1]
			repoPath = repoData[4]

			for x in range(repoData[2][0], repoData[3][0]):

				colPath = os.path.join(self.basePath, repoPath, str(x))
				if not os.path.exists(colPath):
					os.mkdir(colPath)

				for y in range(repoData[2][1], repoData[3][1]):
					
					tilePath = os.path.join(self.basePath, repoPath, str(x), str(y)+".dat")
					#if os.path.exists(tilePath): continue

					tl = slippy.num2deg(x, y, repoZoom)
					br =  slippy.num2deg(x + 1, y + 1, repoZoom)

					commonNode = uuid.uuid4().bytes

					ziggArea = {}
					ziggArea["nodes"] = {}
					nodeId = uuid.uuid4().bytes
					ziggArea["nodes"][nodeId] = [[[[[Interp(tl[0], br[0], .1), Interp(tl[1], br[1], .1), nodeId]],None]],
						{"name": "special place"}]
					ziggArea["ways"] = {}
					ziggArea["ways"][uuid.uuid4().bytes] = [[[[[Interp(tl[0], br[0], .2), Interp(tl[1], br[1], .2), uuid.uuid4().bytes], 
						[Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .5), commonNode], 
						[Interp(tl[0], br[0], .3), Interp(tl[1], br[1], .23), uuid.uuid4().bytes]], None]],
						{"name": "path"}]
					ziggArea["areas"] = {}
					ziggArea["areas"][uuid.uuid4().bytes] = [[[[[Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .4), uuid.uuid4().bytes], 
						[Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .5), commonNode], 
						[Interp(tl[0], br[0], .5), Interp(tl[1], br[1], .5), uuid.uuid4().bytes], 
						[Interp(tl[0], br[0], .5), Interp(tl[1], br[1], .4), uuid.uuid4().bytes]], []]],
						{"name": "test area"}]

					cPickle.dump(ziggArea, open(tilePath, "wt"))



	def _FindRelevantRepos(self, bbox):
		#Find relevant repos
		relevantRepos = []
		for repoName in self.repos:
			repoData = self.repos[repoName]
			repoZoom = repoData[1]
			tl = slippy.num2deg(repoData[2][0], repoData[2][1], repoZoom)
			br =  slippy.num2deg(repoData[3][0], repoData[3][1], repoZoom)

			within = CheckRectOverlap([tl[1], br[0], br[1], tl[0]], bbox)
			if within:
				relevantRepos.append(repoName)
		return relevantRepos

	def _GetTilesFromRepos(self, bbox):

		relevantRepos = self._FindRelevantRepos(bbox)

		#Get tiles from relevant repos
		merged = {"nodes": {}, "ways": {}, "areas": {}, "active": bbox[:]}
		versionInfo = {}

		for repoName in relevantRepos:
			repoData = self.repos[repoName]
			repoZoom = repoData[1]
			repoPath = repoData[4]
			countTiles = 0
			tileVersions = {}
			for x in range(repoData[2][0], repoData[3][0]):
				for y in range(repoData[2][1], repoData[3][1]):
					tl = slippy.num2deg(x, y, repoZoom)
					br =  slippy.num2deg(x + 1, y + 1, repoZoom)
					within = CheckRectOverlap([tl[1], br[0], br[1], tl[0]], bbox)
					if not within: continue

					tilePath = os.path.join(self.basePath, repoPath, str(x), str(y)+".dat")
					if not os.path.exists(tilePath): continue

					tileData = cPickle.load(open(tilePath, "rt"))

					merged["nodes"].update(tileData["nodes"])
					merged["ways"].update(tileData["ways"])
					merged["areas"].update(tileData["areas"])
					countTiles += 1

					if "version" in tileData:
						tileVersions[(x, y)] = tileData["version"]
					else:
						tileVersions[(x, y)] = 1

			versionInfo[repoName] = tileVersions

		return merged, versionInfo

	def _SetTilesInRepos(self, currentArea, area):
		bbox = area["active"]
		relevantRepos = self._FindRelevantRepos(bbox)

		#Update tiles in relevant repos
		bbox = area["active"]
		for repoName in relevantRepos:
			repoData = self.repos[repoName]
			repoZoom = repoData[1]
			repoPath = repoData[4]

			tilesToUpdate = set()

			#Get tiles in active area			
			for x in range(repoData[2][0], repoData[3][0]):
				for y in range(repoData[2][1], repoData[3][1]):
					tl = slippy.num2deg(x, y, repoZoom)
					br =  slippy.num2deg(x + 1, y + 1, repoZoom)
					touchesActive = CheckRectOverlap([tl[1], br[0], br[1], tl[0]], bbox)

					if not touchesActive: continue
					tilesToUpdate.add((x, y))

			#Get tiles that may be affected
			for objType in currentArea:
				if objType == "active": continue
				if objType == "versionInfo": continue
				objDict = currentArea[objType]
				for objId in objDict:
					pts = []
					objData = objDict[objId]
					objShapes, objTags = objData
					for shape in objShapes:
						outer, inners = shape
						pts.extend(outer)
						if inners is None: continue
						for inner in inners:
							pts.extend(outer)

					for pt in pts:
						tilexy = tuple(map(int, slippy.deg2num(pt[0], pt[1], repoZoom)))
						tilesToUpdate.add(tilexy)

			#Update tiles
			for x, y in tilesToUpdate:

				tilePath = os.path.join(self.basePath, repoPath, str(x), str(y)+".dat")
				if not os.path.exists(tilePath): continue

				tileData = cPickle.load(open(tilePath, "rt"))
				if "version" in tileData:
					tileVersion = tileData["version"]
				else:
					tileVersion = 1

				#Remove existing objects that are entirely inside active area
				tileData["nodes"] = FindPartlyOutside(tileData["nodes"], bbox)
				tileData["ways"] = FindPartlyOutside(tileData["ways"], bbox)
				tileData["areas"] = FindPartlyOutside(tileData["areas"], bbox)

				#Add new objects that are entirely inside active area
				nodesInside = FindEntirelyInside(area["nodes"], bbox)
				waysInside = FindEntirelyInside(area["ways"], bbox)
				areasInside = FindEntirelyInside(area["areas"], bbox)

				tileData["nodes"].update(nodesInside)
				tileData["ways"].update(waysInside)
				tileData["areas"].update(areasInside)
			
				#Update objects that are partially outside
				for objId in area["nodes"]:
					if objId in nodesInside: continue
					tileData["nodes"][objId] = area["nodes"][objId]

				for objId in area["ways"]:
					if objId in waysInside: continue
					tileData["ways"][objId] = area["ways"][objId]

				for objId in area["areas"]:
					if objId in areasInside: continue
					tileData["areas"][objId] = area["areas"][objId]

				#Increment version
				tileData["version"] = tileVersion + 1

				#Save result
				cPickle.dump(tileData, open(tilePath, "wt"))

	def GetArea(self, bbox):
		if len(bbox) != 4: 
			raise ValueError("bbox should have 4 values")
		bbox = map(float, bbox)

		if bbox[0] > bbox[2] or bbox[1] > bbox[3]:
			raise ValueError("Invalid bbox")

		merged, versionInfo = self._GetTilesFromRepos(bbox)

		#print merged["nodes"]["'ir\xeem\xa8I\x7f\x83\x06\x1c\xfa\xa8\xd4\x04\xb1"]

		#Trim objects that are not in the requested bbox at all
		merged["nodes"] = Trim(merged["nodes"], bbox)
		merged["ways"] = Trim(merged["ways"], bbox)
		merged["areas"] = Trim(merged["areas"], bbox)
		merged["versionInfo"] = versionInfo

		return merged

	def _GetUuidFromNegId(self, nid, typeChanges):
		if nid not in typeChanges:
			newId = uuid.uuid4().bytes
			typeChanges[nid] = newId
			return newId

		return typeChanges[nid]		

	def _NumberNewObjects(self, objDict, objType, changes):

		keysToRemove = []
		dataToAdd = {}
		typeChanges = changes[objType+"s"]
		nodeChanges = changes["nodes"]

		for ndId in objDict:
			if not isinstance(ndId, int):
				continue
			ndId = int(ndId)
			if ndId >= 0:
				raise ValueError("New objects must have negitive ids")	

			newId = self._GetUuidFromNegId(ndId, typeChanges)
			objData = objDict[ndId]

			#Update dict UUID
			dataToAdd[newId] = objData
			keysToRemove.append(ndId)

		for ndId in objDict:
			objData = objDict[ndId]

			#Update member UUIDs
			shapes, tags = objData
			for shape in shapes:
				outer, inners = shape
				for pt in outer:
					ptId = pt[2]
					if not isinstance(ptId, int):
						continue
					newId = self._GetUuidFromNegId(ptId, nodeChanges)
					pt[2] = newId

				if inners is None: continue
				for inner in inners:
					for pt in inner:
						ptId = pt[2]
						if not isinstance(ptId, int):
							continue
						newId = self._GetUuidFromNegId(ptId, nodeChanges)
						pt[2] = newId

		objDict.update(dataToAdd)
		for k in keysToRemove:
			del objDict[k]

	def _CheckUuidsAlreadyExist(self, newObjsDict, existingObjsDict):
		for objId in newObjsDict:
			#Integers are allowed
			if isinstance(objId, int): continue
			if objId not in existingObjsDict:
				raise ValueError("Unknown UUID referenced")

	def _ValidateUuid(self, i):
		if isinstance(i, int):
			return int(i)
		if i is None:
			return None
		return uuid.UUID(bytes=i).bytes

	def _ValidateLat(self, lat):
		#Check lat lons are within legal bounds
		lat = float(lat)
		if lat < -90. or lat > 90.:
			raise ValueError("Invalid latitude")
		return lat

	def _ValidateLon(self, lon):
		#Check lat lons are within legal bounds
		lon = float(lon)
		if lon < -180. or lon > 180.:
			raise ValueError("Invalid longitude")
		return lon

	def _RewriteInput(self, objDict):
		out = {}
		for objId in objDict:
			objData = objDict[objId]
			outShapeData = []
			outTagData = {}

			shapeData, tagData = objData
			for shape in shapeData:
				outer, inner = shape
				outerOut = []
				innerOut = None

				for pt in outer:
					if len(pt) != 3:
						raise ValueError("Points should have 3 values")
					outerOut.append([self._ValidateLat(pt[0]), self._ValidateLon(pt[1]), self._ValidateUuid(pt[2])])

				if inner is not None:
					innerOut = []
					for innerPoly in inner:
						outInnerPoly = []
						for pt in innerPoly:
							if len(pt) != 3:
								raise ValueError("Points should have 3 values")
							outInnerPoly.append([self._ValidateLat(pt[0]), self._ValidateLon(pt[1]), 
								self._ValidateUuid(pt[2])])
						innerOut.append(outInnerPoly)
				
				outShapeData.append([outerOut, innerOut])
				try:
					tagKeys = tagData.keys()
				except AttributeError:
					raise ValueError("Tag container does not have keys method")

				for tag in tagKeys:
					try:
						val = tagData[tag]
					except:
						raise ValueError("Invalid tag data for key "+str(tag))
					if not isinstance(val, str):
						val = unicode(val)
					if not isinstance(tag, str):
						tag = unicode(tag)
					outTagData[tag] = val
		
			out[self._ValidateUuid(objId)] = [outShapeData, outTagData]

		return out

	def SetArea(self, area, userInfo, debug = None):
		#=Validate input=

		#Get active area
		bbox = area["active"]
		if len(bbox) != 4: 
			raise ValueError("bbox should have 4 values")
		currentArea = self.GetArea(bbox)

		#==Preliminary checks==
		#Rewrite input data to ensure valid types
		newArea = {}
		newArea["active"] = map(float, area["active"][:4])
		newArea["nodes"] = self._RewriteInput(area["nodes"])
		newArea["ways"] = self._RewriteInput(area["ways"])
		newArea["areas"] = self._RewriteInput(area["areas"])

		#Check version info
		if area["versionInfo"] != currentArea["versionInfo"]:
			raise ValueError("Version info does not match")
		
		#Check no UUIDs have been invented by the client
		self._CheckUuidsAlreadyExist(newArea["nodes"], currentArea["nodes"])
		self._CheckUuidsAlreadyExist(newArea["ways"], currentArea["ways"])
		self._CheckUuidsAlreadyExist(newArea["areas"], currentArea["areas"])

		#Check nodes only have one position
		for nodeId in newArea["nodes"]:
			nodeData = newArea["nodes"][nodeId]
			shapeData, tagData = nodeData
			if len(shapeData) != 1:
				raise ValueError("Nodes with only one position supported")
			shape1 = shapeData[0]
			outer1, inner1 = shape1
			if inner1 is not None:
				raise ValueError("Inner shape for a node should be none")
			if len(outer1) != 1:
				raise ValueError("Node shape should have a single point")

			#Check nodes have consistent UUIDs (i.e. one per node)
	 		pt = outer1[0]
			if pt[2] != nodeId:
				raise ValueError("Node UUIDs do not match")

		#Check ways have no inner polys
		for objId in newArea["ways"]:
			objData = newArea["ways"][objId]

			shapeData, tagData = objData
			if len(shapeData) != 1:
				raise ValueError("Ways with only one line is supported")

			outer, inner = shapeData[0]
			if inner is not None:
				raise ValueError("Ways cannot have inner area")

		#Check areas have inner polys
		for objId in newArea["areas"]:
			objData = newArea["areas"][objId]

			shapeData, tagData = objData
			if len(shapeData) != 1:
				raise ValueError("Area with only one outer poly is supported")

			outer, inner = shapeData[0]
			if inner is None:
				raise ValueError("Areas must have list of inner polys (even if it is empty)")

		#Rewrite nodes that are outside active area, so they are in their original positions
		#Any modification of these are silently ignored
		#First collect existing node positions outside active area
		nodePosInsideDict = {}
		nodePosOutsideDict = {}
		for objType in currentArea:
			if objType == "active": continue
			if objType == "versionInfo": continue
			objDict = currentArea[objType]

			for objId in objDict:
				objData = objDict[objId]
				objShapes, objTags = objData
				for shape in objShapes:
					outer, inners = shape
					for pt in outer:

						if not CheckPointInRect(pt, bbox):
							if pt[2] not in nodePosOutsideDict:
								nodePosOutsideDict[pt[2]] = pt

					if inners is None: continue
					for inner in inners:
						for pt in inner:
							if not CheckPointInRect(pt, bbox):
								if pt[2] not in nodePosOutsideDict:
									nodePosOutsideDict[pt[2]] = pt

		#Gather node positions within active area
		for objType in newArea:
			if objType == "active": continue
			if objType == "versionInfo": continue
			objDict = newArea[objType]

			for objId in objDict:
				objData = objDict[objId]
				objShapes, objTags = objData
				for shape in objShapes:
					outer, inners = shape
					for pt in outer:
						if CheckPointInRect(pt, bbox):
							if pt[2] not in nodePosInsideDict:
								nodePosInsideDict[pt[2]] = pt

					if inners is None: continue
					for inner in inners:
						for pt in inner:
							if CheckPointInRect(pt, bbox):
								if pt[2] not in nodePosInsideDict:
									nodePosInsideDict[pt[2]] = pt

		#Update nodes to consistent positions
		for objType in newArea:
			if objType == "active": continue
			if objType == "versionInfo": continue
			objDict = newArea[objType]
			for objId in objDict:
				objData = objDict[objId]
				objShapes, objTags = objData
				for shape in objShapes:

					outer, inners = shape
					for i, pt in enumerate(outer):
						if pt[2] in nodePosOutsideDict:
							outer[i] = nodePosOutsideDict[pt[2]]
						if pt[2] in nodePosInsideDict:
							outer[i] = nodePosInsideDict[pt[2]]
					if inners is not None:
						for inner in inners:
							for i, pt in enumerate(inner):
								if pt[2] in nodePosOutsideDict:
									inner[i] = nodePosOutsideDict[pt[2]]
								if pt[2] in nodePosInsideDict:
									inner[i] = nodePosInsideDict[pt[2]]

		#==All objects that are outside active area must exist in the input==
		partlyOutsideWays = FindPartlyOutside(currentArea["ways"], bbox)

		for wayId in partlyOutsideWays:
			#wayData = partlyOutsideWays[wayId]
			if wayId not in newArea["ways"]:
				raise ValueError("Way in input missing which should still exist")
		
		partlyOutsideAreas = FindPartlyOutside(currentArea["areas"], bbox)

		for areaId in partlyOutsideAreas:
			#areaData = partlyOutsideWays[areaId]
			if wayId not in area["ways"]:
				raise ValueError("Area in input missing which should still exist")
		
		#==Check no shape modifications/deletions/additions are made outside active bbox==
		#All nodes should be witin active area, be existing or not
		partlyOutsideNodes = FindPartlyOutside(area["nodes"], bbox)
		if len(partlyOutsideNodes) > 0:
			raise ValueError("Nodes cannot be added outside active area")	

		#All new ways and area member nodes should be within active area
		for objType in ["ways", "areas"]:
			objDict = area[objType]
			
			for objId in objDict:
				objData = objDict[objId]
				outside = False
				shapeData, tagData = objData
				for shape in shapeData:
					outer, inners = shape
					for pt in outer:
						ptId = pt[2]
						if not isinstance(ptId, int): continue
						
						if not CheckPointInRect(pt, bbox): 
							outside = True
							break

					if inners is None: continue
					for inner in inners:
						for pt in inner:
							ptId = pt[2]
							if not isinstance(ptId, int): continue
							if not CheckPointInRect(pt, bbox): 
								outside = True
								break
				
				if outside:
					raise ValueError("Cannot add nodes outside active area")
		
		#No nodes within way/area should be removed if they are outside active area
		for objType in currentArea:
			if objType == "active": continue
			if objType == "versionInfo": continue
			existingObjDict = currentArea[objType]

			newObjDict = area[objType]
			for objId in existingObjDict:
				if objId not in newObjDict: continue
				objDataExisting = existingObjDict[objId]
				objDataNew = newObjDict[objId]
	
				existingShapeData, existingTagData = objDataExisting
				newShapeData, newTagData = objDataNew
				for existingShape, newShape in zip(existingShapeData, newShapeData):

					outer, inners = existingShape
					newOuter, newInners = newShape

					#Check the nodes we expect in outer way
					outerIds = set()
					for pt in outer:
						if CheckPointInRect(pt, bbox): continue
						outerIds.add(pt[2])

					#Check expected nodes exist in new data
					newIds = set([pt[2] for pt in newOuter])
					for nid in outerIds:
						if nid not in newIds:
							raise ValueError("Cannot add nodes outside active area")

					if inners is None: continue
					for inner, newInner in zip(inners, newInners):
						#Check the nodes we expect in inner way
						innerIds = set()
						for pt in inner:
							if not CheckPointInRect(pt, bbox): continue
							innerIds.add(pt[2])

						#Check expected nodes exist in new data
						newIds = set([pt[2] for pt in newInner])
						for nid in innerIds:
							if nid not in newIds:
								raise ValueError("Cannot add nodes outside active area")
			
		#Ways must have at least one node
		for objId in newArea["ways"]:
			objData = newArea["ways"][objId]
			shapeData, tagData = objData
			for shape in shapeData:
				outer, inners = shape
				if len(outer) < 1:
					raise ValueError("Way must have at least one node")

		#Areas must have at least three nodes in outer way, inner nodes have at least three nodes
		for objId in newArea["areas"]:
			objData = newArea["areas"][objId]
			shapeData, tagData = objData
			for shape in shapeData:
				outer, inners = shape
				if len(outer) < 1:
					raise ValueError("Areas must have at least one node in outer way")
				for inner in inners:
					if len(inner) < 1:
						raise ValueError("Areas must have at least one node in inner way")

		#=Prepare for update=

		#Number new objects
		changes = {"nodes":{}, "ways":{}, "areas":{}}
		self._NumberNewObjects(newArea["nodes"], "node", changes)
		self._NumberNewObjects(newArea["ways"], "way", changes)
		self._NumberNewObjects(newArea["areas"] , "area", changes)

		#=Update working copy=
		#If we have reached here, we are ready to update the working copy

		#print "Updating working copy"
		self._SetTilesInRepos(currentArea, newArea)
		
		
		
		#=Commit with userInfo details=


		return changes


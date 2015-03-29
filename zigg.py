
import cPickle, uuid, config, slippy, os

def CheckRectOverlap(rect1, rect2):
	#left,bottom,right,top

	if rect1[2] < rect2[0]: return 0
	if rect1[0] > rect2[2]: return 0
	if rect1[1] > rect2[3]: return 0
	if rect1[3] < rect2[1]: return 0
	return 1

def CheckPointInRect(pt, rect):
	#left,bottom,right,top

	if pt[1] < rect[0] or pt[1] > rect[2]: return 0
	if pt[0] < rect[1] or pt[0] > rect[3]: return 0
	return 1

def Interp(a, b, frac):
	return a * frac + b * (1. - frac)

class ZiggDb(object):
	
	def __init__(self):
		pass

	def GenerateTestData(self):

		for repoName in config.repos:
			repoData = config.repos[repoName]
			repoZoom = repoData[1]
			repoPath = repoData[4]

			for x in range(repoData[2][0], repoData[3][0]):

				colPath = os.path.join(repoPath, str(x))
				if not os.path.exists(colPath):
					os.mkdir(colPath)

				for y in range(repoData[2][1], repoData[3][1]):
					
					tilePath = os.path.join(repoPath, str(x), str(y)+".dat")
					if os.path.exists(tilePath): continue

					tl = slippy.num2deg(x, y, repoZoom)
					br =  slippy.num2deg(x + 1, y + 1, repoZoom)

					commonNode = uuid.uuid4().bytes

					ziggArea = {}
					ziggArea["nodes"] = {}
					ziggArea["nodes"][uuid.uuid4().bytes] = [[[[[Interp(tl[0], br[0], .1), Interp(tl[1], br[1], .1), None]],None]],
						{"name": "special place"}]
					ziggArea["ways"] = {}
					ziggArea["ways"][uuid.uuid4().bytes] = [[[[[Interp(tl[0], br[0], .2), Interp(tl[1], br[1], .2), None], 
						[Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .5), commonNode], 
						[Interp(tl[0], br[0], .3), Interp(tl[1], br[1], .23), None]], None]],
						{"name": "path"}]
					ziggArea["areas"] = {}
					ziggArea["areas"][uuid.uuid4().bytes] = [[[[[Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .4), None], 
						[Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .5), commonNode], 
						[Interp(tl[0], br[0], .5), Interp(tl[1], br[1], .5), None], 
						[Interp(tl[0], br[0], .5), Interp(tl[1], br[1], .4), None]], []]],
						{"name": "test area"}]

					cPickle.dump(ziggArea, open(tilePath, "wt"))

	def _Trim(self, objsDict, bbox, invert = False):
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

	def _FindRelevantRepos(self, bbox):
		#Find relevant repos
		relevantRepos = []
		for repoName in config.repos:
			repoData = config.repos[repoName]
			repoZoom = repoData[1]
			tl = slippy.num2deg(repoData[2][0], repoData[2][1], repoZoom)
			br =  slippy.num2deg(repoData[3][0], repoData[3][1], repoZoom)

			within = CheckRectOverlap([tl[1], br[0], br[1], tl[0]], bbox)
			if within:
				relevantRepos.append(repoName)
		return relevantRepos

	def _GetTilesFromRepos(self, relevantRepos, bbox):
		#Get tiles from relevant repos
		merged = {"nodes": {}, "ways": {}, "areas": {}, "active": bbox[:]}
		for repoName in relevantRepos:
			repoData = config.repos[repoName]
			repoZoom = repoData[1]
			repoPath = repoData[4]
			for x in range(repoData[2][0], repoData[3][0]):
				for y in range(repoData[2][1], repoData[3][1]):
					tl = slippy.num2deg(x, y, repoZoom)
					br =  slippy.num2deg(x + 1, y + 1, repoZoom)
					within = CheckRectOverlap([tl[1], br[0], br[1], tl[0]], bbox)
					if not within: continue

					tilePath = os.path.join(repoPath, str(x), str(y)+".dat")
					if not os.path.exists(tilePath): continue

					tileData = cPickle.load(open(tilePath, "rt"))

					merged["nodes"].update(tileData["nodes"])
					merged["ways"].update(tileData["ways"])
					merged["areas"].update(tileData["areas"])

		return merged

	def AddUuidsIfMissing(self, objId, objData):

		shapes = objData[0]
		for i, shape in enumerate(shapes):
			outer, inners = shape
			count = 0
			shapeUuid = uuid.uuid3(uuid.UUID(bytes=objId), str(i))

			for j, node in enumerate(outer):
				nodeUuid = node[2]
				if nodeUuid is None:
					node[2] = uuid.uuid3(shapeUuid, str(j)).bytes

			count += 1

			if inners is None: continue
			for inner in inners:
				for j, node in enumerate(outer):
					nodeUuid = node[2]
					if nodeUuid is None:
						node[2] = uuid.uuid3(shapeUuid, str(j)).bytes

				count += 1
		
	def GetArea(self, bbox):
		relevantRepos = self._FindRelevantRepos(bbox)
		merged = self._GetTilesFromRepos(relevantRepos, bbox)

		#Trim objects that are not in the requested bbox at all
		merged["nodes"] = self._Trim(merged["nodes"], bbox)
		merged["ways"] = self._Trim(merged["ways"], bbox)
		merged["areas"] = self._Trim(merged["areas"], bbox)

		#Generate uuids for unnumbered nodes
		for objId in merged["ways"]:
			objData = merged["ways"][objId]
			self.AddUuidsIfMissing(objId, objData)

		return merged

	def _FindPartlyOutside(self, objsDict, bbox):
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

	def SetArea(self, area, userInfo):
		#Validate input

		#Get active area
		bbox = area["active"]
		currentArea = self.GetArea(bbox)

		#All objects that are outside active area must exist in the input
		waysPartlyOutside = self._FindPartlyOutside(area["ways"], bbox)
		areasPartlyOutside = self._FindPartlyOutside(area["areas"], bbox)

		print len(waysPartlyOutside), len(area["ways"])
		print waysPartlyOutside
		print len(areasPartlyOutside), len(area["areas"])
		print areasPartlyOutside


		#Check no shape modifications/deletions/additions are made outside active bbox
		#Shape changes are silently discarded if possible (otherwise we might be comparing floats)

		#Update working copy
		
		#Commit with userInfo details



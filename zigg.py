
import cPickle, uuid, config, slippy, os

def CheckRectOverlap(rect1, rect2):
	#left,bottom,right,top

	if rect1[2] < rect2[0]: return 0
	if rect1[0] > rect2[2]: return 0
	if rect1[1] > rect2[3]: return 0
	if rect1[3] < rect2[1]: return 0
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

					ziggArea = {}
					ziggArea["nodes"] = {}
					ziggArea["nodes"][uuid.uuid4().bytes] = [(Interp(tl[0], br[0], .1), Interp(tl[1], br[1], .1), None), 
						{"name": "special place"}]
					ziggArea["ways"] = {}
					ziggArea["ways"][uuid.uuid4().bytes] = [[(Interp(tl[0], br[0], .2), Interp(tl[1], br[1], .2), None), 
						(Interp(tl[0], br[0], .25), Interp(tl[1], br[1], .21), 1), 
						(Interp(tl[0], br[0], .3), Interp(tl[1], br[1], .23), None)], 
						{"name": "path"}]
					ziggArea["areas"] = {}
					ziggArea["areas"][uuid.uuid4().bytes] = [[(Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .4), None), 
						(Interp(tl[0], br[0], .4), Interp(tl[1], br[1], .5), 1), 
						(Interp(tl[0], br[0], .5), Interp(tl[1], br[1], .5), None), 
						(Interp(tl[0], br[0], .5), Interp(tl[1], br[1], .4), None)], 
						{"name": "test area"}]

					cPickle.dump(ziggArea, open(tilePath, "wt"))


	def GetArea(self, bbox):
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
	
		#Get tiles from relevant repos
		merged = {"nodes": {}, "ways": {}, "areas": {}}
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

		#Trim objects that are not in the requested bbox at all
		#TODO
						
		return merged

	def SetArea(self, areaObj, userInfo):
		#Validate input
		#All objects that are outside allowed area must exist in the input

		#Check no modifications/deletions/additions are made outside specified bbox

		#Update working copy
		
		#Commit with userInfo details


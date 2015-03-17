
import cPickle, uuid

class ZiggArea(object):
	def __init__(self, bbox):
		self.bbox = bbox
		self.basedOnVersion = 1
		self.nodes = []
		self.ways = []
		self.areas = []

class ZiggDb(object):
	
	def __init__(self):
		pass

	def GenerateTestArea(self):

		ziggArea = ZiggArea([-2.,51.,-1.,52.])
		ziggArea.nodes = [[(51., -1.56, None), 
			{"name": "special place", "id": uuid.uuid4().hex}]]
		ziggArea.ways = [[[(51.1, -1.5, None), (51.2, -1.5, 1), (51.3, -1.5, None)], 
			{"name": "path", "id": uuid.uuid4().hex}]]
		ziggArea.areas = [[[(51.1, -1.51, None), (51.2, -1.5, 1), (51.3, -1.51, None), (51.2, -1.52, None)], 
			{"name": "test area", "id": uuid.uuid4().hex}]]
		ziggArea.basedOnVersion = 6
		return ziggArea

	def GetArea(self, bbox):

		ziggArea = cPickle.load(open("area.dat", "rt"))
		return ziggArea

	def SetArea(self, areaObj, userInfo):
		#Validate input
		#All objects that are outside allowed area must exist in the input

		#Check no modifications/deletions/additions are made outside specified bbox

		#Update working copy
		cPickle.dump(areaObj, open("area.dat", "wt"))
		
		#Commit with userInfo details


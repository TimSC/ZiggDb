
#Map stored in area chunks
#No global ids
#Map history available on complete areas, not on individual nodes, ways
#Relations to be limited in maximum allowed area?
#OSM compatibility layer for existing tools
#Multi-polygons stored in native format (not in a relation)
#Ways are stored distinct from areas
#Map is invariant outside of active edit zone (Edits on incomplete data are a pain in the neck!)
#Map data is held in multiple non-overlapping Git repositories
#An object is in a tile iff it has a node within its bounds

import bz2, zigg, cPickle

if __name__ == "__main__":
	ziggDb = zigg.ZiggDb()

	ziggDb.GenerateTestData()

	#area = ziggDb.GetArea([-0.2883911, 51.1517861, -0.2636719, 51.1672889])
	area = ziggDb.GetArea([-0.3, 51.12, -0.19, 51.17])

	#print area
	
	#==Node operations==
	#Basic concept: nodes may only be changed inside the active area

	#Add point within active area (allowed)

	#Move point within active area (allowed)
	
	#Delete point within active area (allowed)

	#Add point outside active area (not allowed)

	#Move point in, from or into outside active area (not allowed)
	
	#Delete point outside active area (not allowed)

	#==Way operations==
	#Basic concept: The shapes of ways outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated

	#Create way within or partly within active area (allowed)

	#Modify tags of way within or partly within active area (allowed)

	#Add or remove nodes from a way that are outside the active area (not allowed)

	#Delete way within active area (allowed)	

	#Delete way partly within or outside active area (not allowed)

	#==Area operations==
	#Basic concept: The shapes of areas outside the active area is constant.
	#Rationale: Shape many be moved into a different data tile; that would be complicated
	

	userInfo = {}
	ziggDb.SetArea(area, userInfo)


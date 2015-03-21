
#Map stored in area chunks
#No global ids
#Map history available on complete areas, not on individual nodes, ways
#Relations to be limited in maximum allowed area?
#OSM compatibility layer for existing tools
#Multi-polygons stored in native format (not in a relation)
#Ways are stored distinct from areas
#Map is invariant outside of active edit zone (Edits on incomplete data are a pain in the neck!)
#Map data is held in multiple non-overlapping Git repositories

import bz2, zigg, cPickle

if __name__ == "__main__":
	ziggDb = zigg.ZiggDb()

	ziggDb.GenerateTestData()

	#area = ziggDb.GetArea([-0.2883911, 51.1517861, -0.2636719, 51.1672889])
	area = ziggDb.GetArea([-0.2883911, 51.1517861, -0.2536719, 51.1672889])

	print area
	

	userInfo = {}
	ziggDb.SetArea(area, userInfo)



#Map stored in area chunks
#No global ids
#Map history available on complete areas, not on individual nodes, ways
#Relations to be limited in maximum allowed area?
#OSM compatibility layer for existing tools
#Multi-polygons stored in native format (not in a relation)
#Ways are stored distinct from areas
#Map is invariant outside of active edit zone (Edits on incomplete data are a pain in the neck!)

import bz2, zigg, cPickle

if __name__ == "__main__":
	ziggDb = zigg.ZiggDb()

	area = ziggDb.GenerateTestArea()
	cPickle.dump(area, open("area.dat", "wt"))

	area = ziggDb.GetArea([])
	
	nd = area.nodes[0]
	nd[0] = (51.9,-1.5, None)

	userInfo = {}
	ziggDb.SetArea(area, userInfo)



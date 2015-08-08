
import zigg, osmapi

class DbContext(object):
    pass

if __name__ == "__main__":
	osmData = {"node": {}, "way": {}, "relation": {}}
	lat = 51.1
	lon = -0.5

	dbHandles = DbContext()
	osmapi.OpenOsmDatabaseHandles(dbHandles)
	idAssignment = None

	osmData["node"][-1] = [(lat, lon), {"foo": "bar"}]
	osmData["node"][-2] = [(lat+0.01, lon), {"foo": "bar2"}]
	osmData["node"][-3] = [(lat+0.01, lon+0.01), {"foo": "bar3"}]
	osmData["node"][-4] = [(lat, lon+0.01), {"foo": "bar4"}]

	osmData["way"][-5] = [[-1, -2, -3, -4], {"foo": "lostroad"}]

	ziggData = osmapi.OsmToZigg(idAssignment, osmData)
	assert(len(ziggData["ways"]) == 1)
	assert(len(ziggData["areas"]) == 0)
	assert(-5 in ziggData["ways"])

	osmData2 = osmapi.ZiggToOsm(idAssignment, ziggData)
	assert(len(osmData2["node"])==4)
	assert(len(osmData2["way"])==1)
	wayObj = osmData2["way"].values()[0]
	assert(len(wayObj[0])==4)

	osmData["way"][-5] = [[-1, -2, -3, -4, -1], {"foo": "lostroad"}]
	ziggData = osmapi.OsmToZigg(idAssignment, osmData)
	assert(len(ziggData["ways"]) == 0)
	assert(len(ziggData["areas"]) == 1)
	assert(-5 in ziggData["areas"])

	osmData2 = osmapi.ZiggToOsm(idAssignment, ziggData)
	assert(len(osmData2["node"])==4)
	assert(len(osmData2["way"])==1)
	wayObj = osmData2["way"].values()[0]
	assert(len(wayObj[0])==5)

	osmData["way"][-5] = [[-1, -2, -3, -4], {"foo": "lostroad", "area": "yes"}]
	ziggData = osmapi.OsmToZigg(idAssignment, osmData)
	assert(len(ziggData["ways"]) == 0)
	assert(len(ziggData["areas"]) == 1)
	assert(-5 in ziggData["areas"])

	osmData2 = osmapi.ZiggToOsm(idAssignment, ziggData)
	assert(len(osmData2["node"])==4)
	assert(len(osmData2["way"])==1)
	wayObj = osmData2["way"].values()[0]
	assert(len(wayObj[0])==4)

	osmData["way"][-5] = [[-1, -2, -3, -4, -1], {"foo": "lostroad", "area": "no"}]
	ziggData = osmapi.OsmToZigg(idAssignment, osmData)
	assert(len(ziggData["ways"]) == 1)
	assert(len(ziggData["areas"]) == 0)
	assert(-5 in ziggData["ways"])

	osmData2 = osmapi.ZiggToOsm(idAssignment, ziggData)
	assert(len(osmData2["node"])==4)
	assert(len(osmData2["way"])==1)
	wayObj = osmData2["way"].values()[0]
	assert(len(wayObj[0])==5)


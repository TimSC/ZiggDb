
import zigg, osmapi

class DbContext(object):
    pass

if __name__ == "__main__":
	osmData = {"node": {}, "way": {}, "relation": {}}
	lat = 51.1
	lon = -0.5

	dbHandles = DbContext()
	osmapi.OpenOsmDatabaseHandles(dbHandles)
	idAssignment = osmapi.IdAssignment(dbHandles)

	osmData["node"][-1] = [(lat, lon), {"foo": "bar"}]

	ziggData = osmapi.OsmToZigg(idAssignment, osmData)


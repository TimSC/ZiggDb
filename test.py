from sqlitedict import SqliteDict
import os

if __name__=="__main__":
	curdir = os.path.dirname(__file__)
	nodeIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'nodeIdToUuidDb.sqlite'), autocommit=True)
	uuidToNodeIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToNodeIdDb.sqlite'), autocommit=True)

	print nodeIdToUuidDb.keys()
	

from sqlitedict import SqliteDict
import os
import config, zigg

if __name__=="__main__":
	curdir = os.path.dirname(__file__)
	nodeIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'nodeIdToUuidDb.sqlite'), autocommit=True)
	uuidToNodeIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToNodeIdDb.sqlite'), autocommit=True)
	nodePosDb = SqliteDict(os.path.join(curdir, 'data', 'nodePosDb.sqlite'), autocommit=True)

	a = nodeIdToUuidDb[902]
	print [a]
	print "pos", nodePosDb[902]
	#print [uuidToNodeIdDb[a]]
	
	#curdir = os.path.dirname(__file__)
	ziggDb = zigg.ZiggDb(config.repos, curdir)
	z = ziggDb.GetArea([-0.27772973684, 51.12376120446, -0.27444191304, 51.12376120446])
	print z


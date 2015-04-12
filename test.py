from sqlitedict import SqliteDict
import os
import config, zigg

if __name__=="__main__":
	curdir = os.path.dirname(__file__)
	nodeIdToUuidDb = SqliteDict(os.path.join(curdir, 'data', 'nodeIdToUuidDb.sqlite'), autocommit=True)
	uuidToNodeIdDb = SqliteDict(os.path.join(curdir, 'data', 'uiidToNodeIdDb.sqlite'), autocommit=True)
	nodePosDb = SqliteDict(os.path.join(curdir, 'data', 'nodePosDb.sqlite'), autocommit=True)

	a = nodeIdToUuidDb[900]
	print [a]
	print "pos", nodePosDb[900]
	#print [uuidToNodeIdDb[a]]
	
	bbox = [-0.28913931169, 51.10731538692, -0.28027453158, 51.112298600129996]
	#curdir = os.path.dirname(__file__)
	ziggDb = zigg.ZiggDb(config.repos, curdir)
	#left,bottom,right,top
	#z = ziggDb.GetArea(bbox)
	#print z

	print bbox
	print zigg.CheckPointInRect([51.10730538692, -0.28028453158], bbox)



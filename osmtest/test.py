from urlutil import *

from sqlitedict import SqliteDict
wayDb = SqliteDict('../data/wayDb.sqlite', autocommit=True)
print wayDb[87]


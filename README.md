# ZiggDb
Another experimental GIS database

* Map stored in area tile chunks
* No global ids
* Map history available on complete areas, not on individual nodes or ways
* Relations to be limited in maximum allowed area?
* OSM compatibility layer for existing tools
* Multi-polygons stored in native format (not in a relation)
* Ways are stored distinct from areas
* Map is invariant outside of active edit zone (Edits on incomplete data are a pain in the neck!)
* Map data is held in multiple non-overlapping Git repositories
* An object is in a tile iff it has a node within its bounds
* UUIDs are generated by the server (to prevent duplicates being deliberately used)

Apache config

  LoadModule wsgi_module modules/mod_wsgi.so

  WSGIScriptAlias /ZiggDb /var/www/ZiggDb/osmapi.py/

  Alias /ZiggDb/static /var/www/ZiggDb/static/
  AddType text/html .py

  <Directory /var/www/ZiggDb/>
      Order deny,allow
      Allow from all
  </Directory>

sudo apt-get install libapache2-mod-wsgi

sudo pip install jinja2 sqlitedict web.py


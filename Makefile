
run:
	# appengine sdk should be in your path, so dev_appserver.py
	# could be found.
	dev_appserver.py --datastore_path=.data/microupdater.datastore\
	         --history_path=.data/microupdater.datastore.history .

.PHONY: run

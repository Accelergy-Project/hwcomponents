pull-latest-submodules:
	git pull
	git submodule update --init --recursive --remote

update-submodules:
	git pull
	git submodule update --init --recursive --remote
	git add models/hwcomponents-*
	git commit -m "Update submodules"
	git push

install-submodules:
	make pull-latest-submodules
	pip3 install models/hwcomponents-*
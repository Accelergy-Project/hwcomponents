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

.PHONY: generate-docs
generate-docs:
    # pip install sphinx-autobuild sphinx_autodoc_typehints sphinx-rtd-theme
	# rm -r docs/_build
	LC_ALL=C.UTF-8 LANG=C.UTF-8 sphinx-apidoc -o docs/source/ hwcomponents
	LC_ALL=C.UTF-8 LANG=C.UTF-8 sphinx-autobuild docs/source docs/_build/html

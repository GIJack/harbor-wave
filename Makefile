PREFIX="/usr/local"
@:
	@echo "Nothing to compile. use install or remove, to...install or remove"
install:
	install -Dm755 harbor_wave.py "$(DESTDIR)/$(PREFIX)/share/harbor-wave/harbor_wave.py"
	install -Dm644 man/harbor-wave.1 "$(DESTDIR)/$(PREFIX)/share/man/man1/harbor-wave.1"
	install -Dm644 bash-completion/harbor-wave "$(DESTDIR)/usr/share/bash-completion/completions/harbor-wave"
	echo "$(PREFIX)/share/harbor-wave/harbor_wave.py \$$@" > "$(DESTDIR)/$(PREFIX)/bin/harbor-wave"
	chmod 755 "$(DESTDIR)/$(PREFIX)/bin/harbor-wave"
	install -Dm644 misc_docs/Commands.md "$(DESTDIR)/$(PREFIX)/share/harbor-wave/docs/Commands.md"
	install -Dm644 misc_docs/Config_Options.md "$(DESTDIR)/$(PREFIX)/share/harbor-wave/docs/Config_Options.md"
	install -Dm644 misc_docs/passing_data_to_droplets.md "$(DESTDIR)/$(PREFIX)/share/harbor-wave/docs/passing_data_to_droplets.md"
	install -Dm755 errata/user-data-init/harborwave_init_meta.py "$(DESTDIR)/$(PREFIX)/share/harbor-wave/errata/user-data-init/harborwave_init_meta.py"
	install -Dm644 errata/user-data-init/harborwave-runonce.service "$(DESTDIR)/$(PREFIX)/share/harbor-wave/errata/user-data-init/harborwave-runonce.service"
	install -Dm644 errata/user-data-init/README.md "$(DESTDIR)/$(PREFIX)/share/harbor-wave/errata/user-data-init/README.md"
	
remove:
	rm -f "$(DESTDIR)/$(PREFIX)/share/harbor-wave/harbor_wave.py"
	rm -f "$(DESTDIR)/$(PREFIX)/share/man/man1/harbor-wave.1"
	rm -f "$(DESTDIR)/usr/share/bash-completion/completions/harbor-wave"
	rm -f "$(DESTDIR)/$(PREFIX)/bin/harbor-wave"
	rm -rf "$(DESTDIR)/$(PREFIX)/share/harborwave/docs"
	rm -rf "$(DESTDIR)/$(PREFIX)/share/harborwave/errata"
	rmdir "$(DESTDIR)/$(PREFIX)/share/harborwave/"

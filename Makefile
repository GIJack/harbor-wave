PREFIX="/usr/local"
@:
	@echo "Nothing to compile. use install or remove, to...install or remove"
install:
	install -Dm755 harbor_wave.py "$(DESTDIR)/$(PREFIX)/share/harbor-wave/harbor_wave.py"
	install -Dm644 man/harbor-wave.1 "$(DESTDIR)/$(PREFIX)/share/man/man1/harbor-wave.1"
	install -Dm644 bash-completion/harbor-wave "$(DESTDIR)/usr/share/bash-completion/completions/harbor-wave"
	echo "$(PREFIX)/share/harbor-wave/harbor_wave.py \$$@" > "$(DESTDIR)/$(PREFIX)/bin/harbor-wave"
	chmod 755 "$(DESTDIR)/$(PREFIX)/bin/harbor-wave"
	
remove:
	rm "$(DESTDIR)/$(PREFIX)/share/harbor-wave/harbor_wave.py"
	rm "$(DESTDIR)/$(PREFIX)/share/man/man1/harbor-wave.1"
	rm "$(DESTDIR)/usr/share/bash-completion/completions/harbor-wave"
	rm "$(DESTDIR)/$(PREFIX)/bin/harbor-wave"

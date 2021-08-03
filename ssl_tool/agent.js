
function hook() {
	if (!Java.available) {
		console.error('Java API not available');
		return;
	}

	Java.perform(function () {
		console.log('hooked');

		////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		var SSL_write, SSL_read;
		const apiResolver = new ApiResolver('module');
		apiResolver.enumerateMatches('exports:*libssl*!SSL_*').forEach(function (v) {
			if (v.name.indexOf('SSL_write') > 0) {
				SSL_write = v.address;
			} else if (v.name.indexOf('SSL_read') > 0) {
				SSL_read = v.address;
			}
		});

		if (SSL_write) {
			Interceptor.attach(SSL_write, {
				onEnter: function (args) {
					this.ssl = args[0].toString();
					this.buf = ptr(args[1]);
				},
				onLeave: function (retval) {
					const len = retval.toInt32();
					if (len > 0) {
						// console.log('SSL_write\n', this.buf.readByteArray(len), '\n', '*'.repeat(120));

						send({
							code: 100,
							ssl: this.ssl
						}, this.buf.readByteArray(len));

						// send({
							// code: 100,
							// ssl: this.ssl
						// }, Memory.readByteArray(this.buf, len));
					}
				}
			});
		}

		if (SSL_read) {
			Interceptor.attach(SSL_read, {
				onEnter: function (args) {
					this.ssl = args[0].toString();
					this.buf = ptr(args[1]);
				},
				onLeave: function (retval) {
					const len = retval.toInt32();
					if (len > 0) {
						// console.log('SSL_read\n', this.buf.readByteArray(len), '\n', '*'.repeat(120));

						send({
							code: 200,
							ssl: this.ssl
						}, this.buf.readByteArray(len));

						// send({
							// code: 200,
							// ssl: this.ssl
						// }, Memory.readByteArray(this.buf, len));
					}
				}
			});
		}
	});
}

hook();

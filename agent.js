
function test() {
	Java.perform(function () {
		console.log('hooked');

		Java.enumerateClassLoaders({
			onMatch: function (loader) {
				try {
					if (loader.findClass('com.alibaba.wireless.security.open.securesignature.a')) {
						// console.log(loader);
						Java.classFactory.loader = loader;
					}
				} catch (e) {
					// console.error('enumerateClassLoaders err', e.stack);
				}
			},
			// DO NOT REMOVE 'onComplete' FUNCTION
			onComplete: function () {
			}
		});

		const a = Java.use('com.alibaba.wireless.security.open.securesignature.a');
		a.signRequest.implementation = function (p0, p1) {
			console.log(Java.retain(this));
			// signRequest = this.signRequest;
			// send('"Got signRequest"');
			return this.signRequest(p0, p1);
		};
	});
}

test();

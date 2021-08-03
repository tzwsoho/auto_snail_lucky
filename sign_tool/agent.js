
var securesignature;

function hook() {
	if (!Java.available) {
		console.error('Java API not available');
		return;
	}

	Java.perform(function () {
		console.log('hooked');

		////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		Java.enumerateClassLoaders({
			onMatch: function (loader) {
				try {
					if (loader.findClass('com.alibaba.wireless.security.open.securesignature.a')) {
						// console.log(loader);
						Java.classFactory.loader = loader;

						Java.use('com.alibaba.wireless.security.open.securesignature.a').signRequest.implementation = function (p0, p1) {
							const ret = this.signRequest(p0, p1);
							if (securesignature) {
								return ret;
							}

							securesignature = Java.retain(this);
							send(1); // notify python script
							return ret;
						};
					}
				} catch (e) {
					// console.error('enumerateClassLoaders err', e.stack);
				}
			},
			// DO NOT REMOVE 'onComplete' FUNCTION
			onComplete: function () {
			}
		});
	});
}

// function stringifyMap(m) {
	// var HashMapEntry = Java.use('java.util.HashMap$HashMapEntry');
	// var entrySet = m.entrySet();
	// var it = entrySet.iterator();
	// var obj = {};
	// while (it.hasNext()) {
		// var node = Java.cast(it.next(), HashMapEntry);
		// var key = node.getKey().toString();
		// var value = node.getValue().toString();
		// obj[key] = value;
	// }

	// return JSON.stringify(obj);
// }

function signRequest(p) {
	// console.log('operationType =', p.operationType);
	// console.log('requestData =', p.requestData);
	// console.log('ts =', p.ts);

	if (!securesignature || !securesignature.signRequest) {
		console.error('securesignature instance not found, please click homepage first!');
		return '';
	}

	const clsSecurityGuardParamContext = Java.use('com.alibaba.wireless.security.open.SecurityGuardParamContext');
	const instSecurityGuardParamContext = clsSecurityGuardParamContext.$new();

	const appKeyField = clsSecurityGuardParamContext.class.getDeclaredField('appKey');
	const requestTypeField = clsSecurityGuardParamContext.class.getDeclaredField('requestType');
	const paramMapField = clsSecurityGuardParamContext.class.getDeclaredField('paramMap');

	// Set fields accessable
	appKeyField.setAccessible(true);
	requestTypeField.setAccessible(true);
	paramMapField.setAccessible(true);

	// Make map
	const HashMap = Java.use("java.util.HashMap");
	const paramHashMap = HashMap.$new();

	const INPUT = `Operation-Type=${p.operationType}&Request-Data=${p.requestData}&Ts=${p.ts}`;
	paramHashMap.put('INPUT', INPUT);

	// Set values
	appKeyField.set(instSecurityGuardParamContext, 'SNAIL_APP_KEY_ANDROID');
	requestTypeField.setInt(instSecurityGuardParamContext, 4);
	paramMapField.set(instSecurityGuardParamContext, paramHashMap);

	// Print values and verify
	// var appKey = appKeyField.get(instSecurityGuardParamContext);
	// var requestType = requestTypeField.get(instSecurityGuardParamContext);
	// var paramMap = paramMapField.get(instSecurityGuardParamContext);
	// console.log(
		// 'appKey =', appKey, '\n',
		// 'requestType =', requestType, '\n',
		// 'paramMap =', stringifyMap(Java.cast(paramMap, HashMap)),
		// '\n', '*'.repeat(100));

	return securesignature.signRequest(instSecurityGuardParamContext, '');
}

hook();

rpc.exports = {
	signRequest,
};

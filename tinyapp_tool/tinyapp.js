
function stringifyMap(m) {
	const Entry = Java.use('java.util.Map$Entry');
	const entrySet = m.entrySet();
	const it = entrySet.iterator();

	var ret = '';
	while (it.hasNext()) {
		const node = Java.cast(it.next(), Entry);
		const key = node.getKey().toString();
		const value = node.getValue().toString();
		ret += key + ': ' + value + '\n';
	}

	return ret;
}

function stringifyArrayList(a) {
	var ret = '';
	for (let i = 0; i < a.size(); i++) {
		ret += a.get(i).toString() + '\n';
	}

	return ret;
}

function hook() {
	if (!Java.available) {
		console.error('Java API not available');
		return;
	}

	Java.perform(function () {
		console.log('hooked');

		////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		const JString = Java.use('java.lang.String');
		const HttpCaller = Java.use('com.alipay.mobile.common.rpc.transport.http.HttpCaller');
		const HttpUrlResponse = Java.use('com.alipay.mobile.common.transport.http.HttpUrlResponse');
		HttpCaller.b.implementation = function (p0) {
			// console.log(p0.toString());
			const ret = this.b(p0);
			const r = Java.cast(ret, HttpUrlResponse);
			const reqBody = JString.$new(p0.e.value);
			const resBody = JString.$new(r.mResData.value);
			const now = new Date();
			const nowStr = now.getFullYear()
				+ '-' + (now.getMonth() + 1).toString().padStart(2, '0')
				+ '-' + now.getDate().toString().padStart(2, '0')
				+ ' ' + now.getHours().toString().padStart(2, '0')
				+ ':' + now.getMinutes().toString().padStart(2, '0')
				+ ':' + now.getSeconds().toString().padStart(2, '0')
				+ '.' + now.getMilliseconds().toString().padEnd(3, '0');
			console.log(JString.format('Time: %s\nRequest: Method: %s URL: %s\nHeaders:\n%s\nTags:\n%s\nBody:\n%s\n\nResponse: Headers:\n%s\nBody:\n%s\n%s',
				[
					nowStr,
					p0.getRequestMethod(),
					p0.getUrl(),
					stringifyArrayList(p0.getHeaders()),
					stringifyMap(p0.getTags()),
					reqBody,
					stringifyMap(r.getHeader().getHeaders()),
					resBody,
					'*'.repeat(120),
				])
			);

			return ret;
		};
	});
}

hook();

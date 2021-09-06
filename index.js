
var GwCookieCacheHelper;

var RpcHelper;

var DeviceInfoUtil;

var transMpaasPropertiesUtil;
var AndroidContext;

var logMpaasPropertiesUtil;

var DeviceUtil;

var SdkVersionUtil;

var LogContext;

var DeviceInfo;

var securesignature;

function findInstanceHook() {
	if (!Java.available) {
		console.error('Java API not available');
		return;
	}

	Java.perform(function () {
		console.log('hooked');

		////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		if (!GwCookieCacheHelper) {
			GwCookieCacheHelper = Java.use('com.alipay.mobile.common.transport.http.GwCookieCacheHelper');
			send(1); // notify python script
		}

		if (!RpcHelper) {
			RpcHelper = Java.use('com.snail.android.lucky.base.api.rpc.utils.RpcHelper');
			send(2); // notify python script
		}

		if (!DeviceInfoUtil) {
			DeviceInfoUtil = Java.use('com.alipay.mobile.common.netsdkextdependapi.deviceinfo.DeviceInfoUtil');
			send(3); // notify python script
		}

		if (!transMpaasPropertiesUtil) {
			transMpaasPropertiesUtil = Java.use('com.alipay.mobile.common.transport.utils.MpaasPropertiesUtil');
			send(4); // notify python script
			// console.log(transMpaasPropertiesUtil.getAppId.overload('android.content.Context'));
		}

		if (!logMpaasPropertiesUtil) {
			logMpaasPropertiesUtil = Java.use('com.alipay.mobile.common.logging.util.MpaasPropertiesUtil');
			send(5); // notify python script
		}

		if (!DeviceUtil) {
			DeviceUtil = Java.use('com.snail.android.lucky.base.api.utils.DeviceUtil');
			send(6); // notify python script
		}

		if (!SdkVersionUtil) {
			SdkVersionUtil = Java.use('com.alipay.mobile.common.logging.api.utils.SdkVersionUtil');
			send(7); // notify python script
		}

		if (!LogContext) {
			const LoggerFactory = Java.use('com.alipay.mobile.common.logging.api.LoggerFactory');
			LogContext = LoggerFactory.getLogContext.call(LoggerFactory);
			send(8); // notify python script
		}

		if (!DeviceInfo) {
			DeviceInfo = Java.use('com.alipay.mobile.common.info.DeviceInfo');
			send(9); // notify python script
		}

		Java.use('com.alipay.mobile.common.rpc.transport.http.HttpCaller').$init.implementation = function (p0, p1, p2, p3, p4, p5, p6, p7) {
			const ret = this.$init(p0, p1, p2, p3, p4, p5, p6, p7);
			if (AndroidContext) {
				return ret;
			}

			AndroidContext = Java.retain(p6);
			send(10); // notify python script
			return ret;
		};

		////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

		Java.enumerateClassLoaders({
			onMatch: function (loader) {
				try {
					if (loader.findClass('com.alibaba.wireless.security.open.securesignature.a')) {
						Java.classFactory.loader = loader;

						Java.use('com.alibaba.wireless.security.open.securesignature.a').signRequest.implementation = function (p0, p1) {
							const ret = this.signRequest(p0, p1);
							if (securesignature) {
								return ret;
							}

							securesignature = Java.retain(this);
							send(11); // notify python script
							return ret;
						}
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

function getCookie() {
	if (!GwCookieCacheHelper) {
		console.error('GwCookieCacheHelper instance not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (GwCookieCacheHelper.getCookie) {
		const cookie = GwCookieCacheHelper.getCookie.call(GwCookieCacheHelper, '.shulidata.com');
		if (cookie) {
			return cookie.toString();
		}
	}

	return '';
}

function getRpcBaseInfo() {
	if (!RpcHelper) {
		console.error('RpcHelper instance not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (RpcHelper.getRpcBaseInfo) {
		const rpcBaseInfo = RpcHelper.getRpcBaseInfo.call(RpcHelper);
		if (rpcBaseInfo) {
			return rpcBaseInfo.toString();
		}
	}

	return '';
}

function getDeviceId() {
	if (!DeviceInfoUtil) {
		console.error('DeviceInfoUtil instance not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (DeviceInfoUtil.getDeviceId) {
		const deviceId = DeviceInfoUtil.getDeviceId.call(DeviceInfoUtil);
		if (deviceId) {
			return deviceId.toString();
		}
	}

	return '';
}

function getAppId() {
	if (!AndroidContext || !transMpaasPropertiesUtil) {
		console.error('AndroidContext/transMpaasPropertiesUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (transMpaasPropertiesUtil.getAppId) {
		const appId = transMpaasPropertiesUtil.getAppId.overload('android.content.Context').call(transMpaasPropertiesUtil, AndroidContext);
		if (appId) {
			return appId.toString();
		}
	}

	return '';
}

function getAppKeyFromMetaData() {
	if (!AndroidContext || !transMpaasPropertiesUtil) {
		console.error('AndroidContext/transMpaasPropertiesUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (transMpaasPropertiesUtil.getAppKeyFromMetaData) {
		const appKeyFromMetaData = transMpaasPropertiesUtil.getAppKeyFromMetaData(AndroidContext);
		if (appKeyFromMetaData) {
			return appKeyFromMetaData.toString();
		}
	}

	return '';
}

function getWorkspaceId() {
	if (!AndroidContext || !logMpaasPropertiesUtil) {
		console.error('AndroidContext/logMpaasPropertiesUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (logMpaasPropertiesUtil.getWorkSpaceId) {
		const workspaceId = logMpaasPropertiesUtil.getWorkSpaceId.call(logMpaasPropertiesUtil, AndroidContext);
		if (workspaceId) {
			return workspaceId.toString();
		}
	}

	return '';
}

function getVersion() {
	if (!SdkVersionUtil) {
		console.error('SdkVersionUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (SdkVersionUtil.getVersion) {
		const version = SdkVersionUtil.getVersion('com.alipay.android.phone.mobilesdk.rpc.BuildConfig');
		if (version) {
			return version.toString().split(':')[1];
		}
	}

	return '';
}

function getImei() {
	if (!AndroidContext || !DeviceUtil) {
		console.error('AndroidContext/DeviceUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (DeviceUtil.getImei) {
		const imei = DeviceUtil.getImei.call(DeviceUtil, AndroidContext);
		if (imei) {
			return imei.toString();
		}
	}

	return '';
}

function getCheckAndroidId() {
	if (!AndroidContext || !DeviceUtil) {
		console.error('AndroidContext/DeviceUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (DeviceUtil.getCheckAndroidID) {
		const checkAndroidID = DeviceUtil.getCheckAndroidID.call(DeviceUtil, AndroidContext);
		if (checkAndroidID) {
			return checkAndroidID.toString();
		}
	}

	return '';
}

function getAppVersion() {
	if (!DeviceUtil) {
		console.error('DeviceUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (DeviceUtil.getAppVersion) {
		const appVersion = DeviceUtil.getAppVersion.call(DeviceUtil);
		if (appVersion) {
			return appVersion.toString();
		}
	}

	return '';
}

function getChannelId() {
	if (!LogContext) {
		console.error('LogContext not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (LogContext.getChannelId) {
		const channelId = LogContext.getChannelId();
		if (channelId) {
			return channelId.toString();
		}
	}

	return '';
}

function getMac() {
	if (!AndroidContext || !DeviceInfo) {
		console.error('AndroidContext/DeviceInfo not found, please restart JiYang and click homepage first!');
		return '';
	}

	if (DeviceInfo.createInstance) {
		const cInstance = DeviceInfo.createInstance.call(DeviceInfo, AndroidContext);
		if (cInstance) {
			const macAddress = cInstance.getMacAddress();
			if (macAddress) {
				return macAddress.toString();
			}
		}
	}

	return '';
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

findInstanceHook();

rpc.exports = {
	getCookie,
	getRpcBaseInfo,
	getDeviceId,
	getAppId,
	getAppKeyFromMetaData,
	getVersion,
	getImei,
	getCheckAndroidId,
	getAppVersion,
	getChannelId,
	getMac,
	getWorkspaceId,
	signRequest,
};

// console.log(Module.findExportByName('libart.so', 'JNI_GetCreatedJavaVMs'));

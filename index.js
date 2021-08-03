
var GwCookieCacheHelper;

var RpcHelper;

var DeviceInfoUtil;

var transMpaasPropertiesUtil;
var AndroidContext;

var logMpaasPropertiesUtil;

var DeviceUtil;
var LauncherApplicationAgent;
var ApplicationContext;

var SdkVersionUtil;

var LogContext;

var DeviceInfo;

var securesignature;

function findInstanceHook() {
	if (GwCookieCacheHelper || RpcHelper || securesignature) {
		return;
	}

	if (!Java.available) {
		console.error('Java API not available');
		return;
	}

	Java.perform(function () {
		console.log('hooked');

		Java.use('com.alipay.mobile.common.transport.http.GwCookieCacheHelper').getCookie.implementation = function (p0) {
			const ret = this.getCookie(p0);
			if (GwCookieCacheHelper) {
				return ret;
			}

			GwCookieCacheHelper = Java.retain(this);
			send(1); // notify python script
			return ret;
		};

		Java.use('com.snail.android.lucky.base.api.rpc.utils.RpcHelper').getRpcBaseInfo.implementation = function () {
			const ret = this.getRpcBaseInfo();
			if (RpcHelper) {
				return ret;
			}

			RpcHelper = Java.retain(this);
			send(2); // notify python script
			return ret;
		};

		Java.use('com.alipay.mobile.common.netsdkextdependapi.deviceinfo.DeviceInfoUtil').getDeviceId.implementation = function () {
			const ret = this.getDeviceId();
			if (DeviceInfoUtil) {
				return ret;
			}

			DeviceInfoUtil = Java.retain(this);
			send(3); // notify python script
			return ret;
		};

		if (!transMpaasPropertiesUtil) {
			transMpaasPropertiesUtil = Java.use('com.alipay.mobile.common.transport.utils.MpaasPropertiesUtil');
			send(4); // notify python script
			// console.log(transMpaasPropertiesUtil.getAppId.overload('android.content.Context'));
			// console.log(transMpaasPropertiesUtil.getAppKeyFromMetaData);
		}

		if (!logMpaasPropertiesUtil) {
			logMpaasPropertiesUtil = Java.use('com.alipay.mobile.common.logging.util.MpaasPropertiesUtil');
			send(5); // notify python script
			// console.log(logMpaasPropertiesUtil.getWorkSpaceId);
		}

		Java.use('com.alipay.mobile.common.rpc.transport.http.HttpCaller').$init.implementation = function (p0, p1, p2, p3, p4, p5, p6, p7) {
			const ret = this.$init(p0, p1, p2, p3, p4, p5, p6, p7);
			if (AndroidContext) {
				return ret;
			}

			AndroidContext = Java.retain(p6);
			send(6); // notify python script
			return ret;
		};

		if (!DeviceUtil) {
			DeviceUtil = Java.use('com.snail.android.lucky.base.api.utils.DeviceUtil');
			send(7); // notify python script
		}

		if (!LauncherApplicationAgent) {
			LauncherApplicationAgent = Java.use('com.alipay.mobile.framework.LauncherApplicationAgent');
			LauncherApplicationAgent.getInstance.implementation = function () {
				const ret = this.getInstance.call(LauncherApplicationAgent);
				if (ApplicationContext) {
					return ret;
				}

				ApplicationContext = Java.retain(ret.getApplicationContext());
				send(8); // notify python script
				return ret;
			}
		}

		if (!SdkVersionUtil) {
			SdkVersionUtil = Java.use('com.alipay.mobile.common.logging.api.utils.SdkVersionUtil');
			send(9); // notify python script
		}

		if (!LogContext) {
			const LoggerFactory = Java.use('com.alipay.mobile.common.logging.api.LoggerFactory');
			LogContext = LoggerFactory.getLogContext.call(LoggerFactory);
			send(10); // notify python script
		}

		if (!DeviceInfo) {
			DeviceInfo = Java.use('com.alipay.mobile.common.info.DeviceInfo');
			send(11); // notify python script
		}

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
							send(12); // notify python script
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
	if (!GwCookieCacheHelper || !GwCookieCacheHelper.getCookie) {
		console.error('GwCookieCacheHelper instance not found, please restart JiYang and click homepage first!');
		return '';
	}

	return GwCookieCacheHelper.getCookie('.shulidata.com').toString();
}

function getRpcBaseInfo() {
	if (!RpcHelper || !RpcHelper.getRpcBaseInfo) {
		console.error('RpcHelper instance not found, please restart JiYang and click homepage first!');
		return '';
	}

	return RpcHelper.getRpcBaseInfo().toString();
}

function getDeviceId() {
	if (!DeviceInfoUtil || !DeviceInfoUtil.getDeviceId) {
		console.error('DeviceInfoUtil instance not found, please restart JiYang and click homepage first!');
		return '';
	}

	return DeviceInfoUtil.getDeviceId().toString();
}

function getAppId() {
	if (!AndroidContext || !transMpaasPropertiesUtil) {
		console.error('AndroidContext/transMpaasPropertiesUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	return transMpaasPropertiesUtil.getAppId.overload('android.content.Context').call(transMpaasPropertiesUtil, AndroidContext).toString();
}

function getAppKeyFromMetaData() {
	if (!AndroidContext || !transMpaasPropertiesUtil) {
		console.error('AndroidContext/transMpaasPropertiesUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	return transMpaasPropertiesUtil.getAppKeyFromMetaData(AndroidContext).toString();
}

function getWorkspaceId() {
	if (!AndroidContext || !logMpaasPropertiesUtil) {
		console.error('AndroidContext/logMpaasPropertiesUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	return logMpaasPropertiesUtil.getWorkSpaceId.call(logMpaasPropertiesUtil, AndroidContext).toString();
}

function getVersion() {
	if (!SdkVersionUtil) {
		console.error('SdkVersionUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	return SdkVersionUtil.getVersion('com.alipay.android.phone.mobilesdk.rpc.BuildConfig').toString().split(':')[1];
}

function getImei() {
	if (!ApplicationContext || !DeviceUtil) {
		console.error('ApplicationContext/DeviceUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	return DeviceUtil.getImei.call(DeviceUtil, ApplicationContext).toString();
}

function getCheckAndroidId() {
	if (!ApplicationContext || !DeviceUtil) {
		console.error('ApplicationContext/DeviceUtil not found, please restart JiYang and click homepage first!');
		return '';
	}

	return DeviceUtil.getCheckAndroidID.call(DeviceUtil, ApplicationContext).toString();
}

function getChannelId() {
	if (!LogContext) {
		console.error('LogContext not found, please restart JiYang and click homepage first!');
		return '';
	}

	return LogContext.getChannelId().toString();
}

function getMac() {
	if (!ApplicationContext || !DeviceInfo) {
		console.error('ApplicationContext/DeviceInfo not found, please restart JiYang and click homepage first!');
		return '';
	}

	return DeviceInfo.createInstance.call(DeviceInfo, ApplicationContext).getMacAddress().toString();
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
	getChannelId,
	getMac,
	getWorkspaceId,
	signRequest,
};

// console.log(Module.findExportByName('libart.so', 'JNI_GetCreatedJavaVMs'));

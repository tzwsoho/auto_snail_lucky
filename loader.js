
'use strict';

const frida = require('frida');
const fs = require('fs');

var session, script;

process.on('SIGINT', function () {
	if (session) {
		session.detach();
	}

	process.exit();
});

process.on('uncaughtException', function (err, origin) {
	console.error(err)
	console.error(origin)
});

process.on('exit', function (code) {
	console.log('退出码：%d', code);
});

async function getUSBDevice() {
	return await frida.getUsbDevice();
}

async function getSnailLuckyPID(device) {
	const processes = await device.enumerateProcesses();
	// processes.forEach(v => { console.log(v); });

	const snailLucky = processes.find(v => v.name.indexOf('几羊') >= 0);
	return snailLucky && snailLucky.pid || 0;
}

async function launchSnailLucky(device) {
	const pidSnailLucky = await device.spawn('com.snail.android.lucky');
	await device.resume(pidSnailLucky);
	return pidSnailLucky;
}

async function runScript(pid) {
	const file = fs.readFileSync(require.resolve('./index.js'), 'utf8');
	session = await frida.attach(pid);
	script = await session.createScript(file);
	script.message.connect(onMessage);
	await script.load();
}

async function onMessage(message, payload) {
	console.log(message, payload);

	if (!script) {
		return;
	}

	// if (1 === message) {
	// 	// sign = 3e57cdc455d7cd2babad8b32432f1346
	// 	console.log(await script.exports.sign('alipay.mobile.aggrbillinfo.drm.client.info', 'W3siYXBkaWQiOiJlWU9Ja3FYWEk0N0pXYjhjbjZEMG94YVU2aHBJd1RFWmFSVk9Wc0pZVDRQVnJidUNFZXAwUlFCRyIsImNsaWVudEtleSI6Im91RkNLR3FvUHoiLCJjbGllbnRWZXJzaW9uIjoiMy40LjAuNjkiLCJtb2RlbCI6Ik5YNTYzSiIsInBsYXRmb3JtIjoiQW5kcm9pZCIsInRva2VuIjoiMjUxYTVjMDQ3NTVkMGVhMDU1YjE5MTc3OWIwMWQ0NzMiLCJ1c2VySWQiOiI4MDg4MDE1MDYwOTMyMzEyIiwidXRkaWQiOiJVSkRKS3hpRXgxZ0RBRklVb0xrQTB1eHgifV0=', 'NgZEBey'));
	// }
}

(async () => {
	const device = await getUSBDevice();
	if (!device) {
		console.error('请先连接手机并启动 frida-server');
		return;
	}

	let pidSnailLucky = await getSnailLuckyPID(device);
	if (pidSnailLucky === 0) { // 进程未启动
		pidSnailLucky = await launchSnailLucky(device);
		if (pidSnailLucky === 0) { // 进程启动失败
			console.error('几羊程序启动失败，请确认手机已安装此 APP');
			return;
		}
	}

	// console.log(pidSnailLucky);

	await runScript(pidSnailLucky);
})();

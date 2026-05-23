const fs = require("fs");

const core = fs.readFileSync("web/resources/static/js/moechat_core.js", "utf8");
const failures = [];

if (!core.includes("blobToWavDataUrl(blob)")) {
  failures.push("recorded browser audio must be converted to WAV before /api/asr");
}
if (!core.includes("audioBufferToWavBlob")) {
  failures.push("missing WAV encoder for browser MediaRecorder output");
}
if ((core.match(/new EventSource/g) || []).length !== 1) {
  failures.push("chat stream handling should be centralized in startChatStream");
}
if (!core.includes("showErrorMessage('聊天连接中断，请稍后重试。')")) {
  failures.push("SSE connection errors must be visible to the user");
}
if (!core.includes("showErrorMessage('语音识别失败，请检查麦克风权限或稍后重试。')")) {
  failures.push("ASR failures must be visible to the user");
}
if (!core.includes("recordBtn.disabled = true") || !core.includes("recordBtn.disabled = false")) {
  failures.push("record button state must be managed around microphone availability");
}

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

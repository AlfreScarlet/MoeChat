const fs = require("fs");

const core = fs.readFileSync("web/resources/static/js/moechat_core.js", "utf8");
const css = fs.readFileSync("web/resources/static/css/moechat_style.css", "utf8");

const failures = [];

if (core.includes("div.innerHTML =")) {
  failures.push("appendMessage must not write user/model text through div.innerHTML");
}
if (!core.includes("document.createTextNode")) {
  failures.push("appendMessage should render text through text nodes");
}
if (!core.includes('rainScript.src = "/js/rain_effect.js"')) {
  failures.push("rain effect script path must point at /js/rain_effect.js");
}
if (!css.includes('url("/image/crack_overlay.png")')) {
  failures.push("crack overlay CSS must point at /image/crack_overlay.png");
}

if (failures.length > 0) {
  console.error(failures.join("\n"));
  process.exit(1);
}

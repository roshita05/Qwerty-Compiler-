"use strict";
const $ = (id) => document.getElementById(id);
const examples = {
  demo: `# Welcome to your own programming language.\nkeep name = "QWERTY";\nsayit(concatit("Hello from ", name, "!"));\n\nkeep a = 20;\nkeep b = 5;\nsayit("Addition:", addit(a, b));\nsayit("Subtraction:", subit(a, b));\n\nkeep marks = [78, 92, 85, 92, 66];\nsayit("Average:", avgit(marks));\nsayit("Unique:", uniqueit(marks));\n\nwhen avgit(marks) > 80 {\n    sayit("You are doing great!");\n} otherwise {\n    sayit("Keep learning!");\n}\n\neach n over spanit(1, 4) {\n    sayit("Square of", n, "=", powerit(n, 2));\n}\n`,
  recursion: `# Functions are declared with craft; give returns.\ncraft factorialq(n) {\n    when n <= 1 { give 1; }\n    give multit(n, factorialq(subit(n, 1)));\n}\n\neach n over spanit(1, 8) {\n    sayit(n, "factorial =", factorialq(n));\n}\n\nassertit(equalit(factorialq(5), 120));\n`,
  loops: `keep counter = 0;\nwhilst counter < 6 {\n    counter = addit(counter, 1);\n    when counter == 2 { skip; }\n    when counter == 5 { stop; }\n    sayit("Counter:", counter);\n}\n\nkeep total = 0;\neach item over [10, 20, 30] {\n    total = addit(total, item);\n}\nsayit("Total:", total);\n`,
  collections: `# Updates return new collections. Assign the result.\nkeep items = [3, 1, 2];\nitems = pushit(items, 4);\nsayit("Sorted:", sortit(items));\nsayit("Reversed:", reverseit(items));\n\nkeep profile = mapit(["name"], ["Ada"]);\nprofile = setit(profile, "language", "QWERTY");\neach key over keysit(profile) {\n    sayit(key, "=", getit(profile, key));\n}\n`,
  input: `# Fill Program input with two lines before running.\nkeep name = askit("Your name: ");\nsayit(name);\nkeep age = intit(askit("Your age: "));\nsayit(age);\nsayit(concatit("Hello, ", name, "!"));\nsayit("Next year you will be", addit(age, 1));\n`,
  error: `# This intentional error points to the failing call.\nkeep numerator = 10;\nkeep denominator = 0;\nsayit(divit(numerator, denominator));\n`
};
const keywords = new Set("keep craft give when otherwise whilst each over stop skip aye nay void".split(" "));
let functions = [], functionNames = new Set(), busy = false, saveTimer, toastTimer;
const sourceEditor = $("editor");
function toast(message) { $("toast").textContent = message; $("toast").hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $("toast").hidden = true, 2400); }
function highlight() {
  const source = sourceEditor.value;
  const fragment = document.createDocumentFragment();
  const pattern = /#[^\n]*|\/\*[\s\S]*?(?:\*\/|$)|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b|\b[A-Za-z_][A-Za-z_0-9]*\b/g;
  let end = 0;
  for (const match of source.matchAll(pattern)) {
    fragment.append(document.createTextNode(source.slice(end, match.index)));
    const value = match[0];
    let type = value.startsWith("#") || value.startsWith("/*") ? "comment" : /^["']/.test(value) ? "string" : /^\d/.test(value) ? "number" : keywords.has(value) ? "keyword" : functionNames.has(value) ? "function" : "";
    const element = document.createElement("span");
    if (type) element.className = `tok-${type}`;
    element.textContent = value;
    fragment.append(element);
    end = match.index + value.length;
  }
  fragment.append(document.createTextNode(source.slice(end) + "\n"));
  $("highlight").replaceChildren(fragment);
  $("lines").textContent = Array.from({length: source.split("\n").length}, (_, i) => i + 1).join("\n") + "\n";
  syncScroll(); cursor();
}
function syncScroll() { $("highlight").scrollTop = sourceEditor.scrollTop; $("highlight").scrollLeft = sourceEditor.scrollLeft; $("lines").scrollTop = sourceEditor.scrollTop; }
function cursor() { const before = sourceEditor.value.slice(0, sourceEditor.selectionStart).split("\n"); $("cursor").textContent = `Ln ${before.length}, Col ${before.at(-1).length + 1}`; }
function changed() { highlight(); $("saved").textContent = "saving..."; clearTimeout(saveTimer); saveTimer = setTimeout(() => { try { localStorage.setItem("qwerty-source-v1", sourceEditor.value); $("saved").textContent = "saved locally"; } catch { $("saved").textContent = "unsaved draft"; } }, 400); }
function switchTab(tab) {
  const consoleActive = tab === "console";
  $("console").hidden = !consoleActive; $("bytecode").hidden = consoleActive;
  for (const name of ["console", "bytecode"]) { const active = name === tab; $(`${name}-tab`).classList.toggle("active", active); $(`${name}-tab`).setAttribute("aria-selected", String(active)); }
}
function setStatus(message, error = false) { $("status").classList.toggle("error", error); $("status").replaceChildren(); const dot = document.createElement("span"); dot.className = "status-dot"; $("status").append(dot, document.createTextNode(message)); }
async function execute(action) {
  if (busy) return;
  busy = true; $("run").disabled = $("check").disabled = true;
  setStatus(action === "run" ? "Compiling and running..." : "Checking your program...");
  $("diagnostic").hidden = true; $("diagnostic").textContent = "";
  $("output").textContent = ""; $("bytecode").textContent = "No instructions available for this attempt.";
  switchTab("console");
  const start = performance.now();
  try {
    const response = await fetch("/api/execute", {method: "POST", headers: {"Content-Type": "application/json", "X-Qwerty-Token": document.querySelector('meta[name="qwerty-token"]').content}, body: JSON.stringify({source: sourceEditor.value, input: $("program-input").value, action}), signal: AbortSignal.timeout(12000)});
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.error === "string" ? data.error : "The local server rejected this request.");
    $("output").textContent = data.output || (data.ok ? action === "check" ? "Syntax, names, function calls, and control flow are valid.\n\nDynamic types and runtime values are checked during execution." : "Program finished with no output." : "");
    if (data.bytecode) $("bytecode").textContent = data.bytecode;
    if (data.ok) setStatus(`${action === "check" ? "Check passed" : "Execution complete"}  /  ${Math.round(performance.now() - start)} ms${action === "run" ? `  /  ${data.steps.toLocaleString()} instructions` : ""}`);
    else { setStatus("Program stopped with a diagnostic", true); $("diagnostic").textContent = data.error.formatted; $("diagnostic").hidden = false; }
  } catch (error) { setStatus("Connection or execution failed", true); $("diagnostic").textContent = `${error.message}\nCheck that the local Python server is still running.`; $("diagnostic").hidden = false; }
  finally { busy = false; $("run").disabled = $("check").disabled = false; }
}
function renderFunctions() {
  const query = $("search").value.toLowerCase();
  const visible = functions.filter(f => `${f.name} ${f.category} ${f.description}`.toLowerCase().includes(query));
  const fragment = document.createDocumentFragment(); let category = "";
  for (const fn of visible) {
    if (fn.category !== category) { category = fn.category; const label = document.createElement("div"); label.className = "function-group"; label.textContent = category; fragment.append(label); }
    const button = document.createElement("button"); button.className = "function-item"; button.textContent = fn.name;
    const paren = document.createElement("span"); paren.className = "fn-paren"; paren.textContent = "()"; button.append(paren);
    button.title = `${fn.signature}\n${fn.description}\nInsert: ${fn.example}`;
    button.addEventListener("click", () => { sourceEditor.setRangeText(fn.example, sourceEditor.selectionStart, sourceEditor.selectionEnd, "end"); sourceEditor.focus(); changed(); toast(`Inserted ${fn.name}() example`); });
    fragment.append(button);
  }
  if (!visible.length) { const empty = document.createElement("p"); empty.className = "muted"; empty.textContent = "No matching functions."; fragment.append(empty); }
  $("function-list").replaceChildren(fragment);
}
sourceEditor.addEventListener("input", changed); sourceEditor.addEventListener("scroll", syncScroll); sourceEditor.addEventListener("click", cursor); sourceEditor.addEventListener("keyup", cursor);
sourceEditor.addEventListener("keydown", event => { if (event.key === "Tab") { event.preventDefault(); sourceEditor.setRangeText("    ", sourceEditor.selectionStart, sourceEditor.selectionEnd, "end"); changed(); } });
document.addEventListener("keydown", event => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); execute("run"); } });
$("run").addEventListener("click", () => execute("run")); $("check").addEventListener("click", () => execute("check"));
$("console-tab").addEventListener("click", () => switchTab("console")); $("bytecode-tab").addEventListener("click", () => switchTab("bytecode"));
$("clear").addEventListener("click", () => { $("output").textContent = ""; $("diagnostic").hidden = true; $("bytecode").textContent = "Compile or run your program to inspect its instructions."; setStatus("Ready to build"); });
$("search").addEventListener("input", renderFunctions);
$("examples").addEventListener("change", () => { if (sourceEditor.value.trim() && !confirm("Replace the current editor contents with this example? Save your .qw file first to keep it.")) return; sourceEditor.value = examples[$("examples").value]; if ($("examples").value === "input") $("program-input").value = "Ada\n25"; sourceEditor.scrollTop = 0; changed(); });
$("download").addEventListener("click", () => { const url = URL.createObjectURL(new Blob([sourceEditor.value], {type: "text/plain;charset=utf-8"})); const link = document.createElement("a"); link.href = url; link.download = "playground.qw"; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); });
try { sourceEditor.value = localStorage.getItem("qwerty-source-v1") || examples.demo; } catch { sourceEditor.value = examples.demo; }
highlight();
fetch("/api/functions").then(response => { if (!response.ok) throw new Error("Library request failed"); return response.json(); }).then(data => { functions = data.functions; functionNames = new Set(functions.map(f => f.name)); $("function-count").textContent = functions.length; renderFunctions(); highlight(); }).catch(() => toast("Function reference unavailable. Check the local server."));

import re
path = '/Users/ns/Projects/ns-agent/NsAgent-jiagou.html'
with open(path, 'r') as f:
    lines = f.readlines()

# Replace line 2337 (index 2336)
new_line = 'function switchVersion(v){["v010","v020","v030","v040"].forEach(function(x){document.getElementById("btn-"+x).classList.toggle("active",v===x)});var L={v010:"v0.1.0",v020:"v0.2.0",v030:"v0.3.0",v040:"v0.4.0"},S={v010:"9 文件",v020:"16 文件",v030:"24 文件",v040:"33 文件"};document.getElementById("ver-info").innerHTML="当前 <b>"+L[v]+"</b> — "+S[v];document.querySelectorAll("[data-versions]").forEach(function(el){var vs=el.getAttribute("data-versions");if(vs.indexOf(v)===-1)el.classList.add("hidden-version");else el.classList.remove("hidden-version")});document.body.className=v+"-view"}switchVersion("v040");\n'

old = lines[2336]
lines[2336] = new_line
print(f'Replaced line. Old had {"v040" in old}, new has {"v040" in new_line}')

with open(path, 'w') as f:
    f.writelines(lines)

# Verify
with open(path, 'r') as f:
    c = f.read()
has_v040_switch = 'switchVersion("v040")' in c
has_v040_files = 'v040:"33 文件"' in c or 'v040":"33' in c
print(f'switchVersion v040: {has_v040_switch}')
print(f'v040 33 files: {has_v040_files}')
print(f'Size: {len(c)} bytes')

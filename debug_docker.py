"""Debug Docker container log output for both simple and multi-line code."""
import json, tempfile, os, platform, docker

client = docker.from_env()

for label, code in [
    ('simple', 'x = 1 + 1'),
    ('multi', 'def add(a, b):\n    return a + b\nresult = add(1, 2)'),
]:
    wrapper = f'''import json
result = {{"success": False, "error": None}}
try:
    exec(compile({repr(code)}, "<codeguard>", "exec"))
    result["success"] = True
except Exception as e:
    result["error"] = str(e)
print(json.dumps(result))
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(wrapper)
        tf = f.name

    tdir = os.path.dirname(tf)
    if platform.system() == 'Windows':
        tdir = tdir.replace('\\', '/')
        if len(tdir) >= 2 and tdir[1] == ':':
            tdir = '/' + tdir[0].lower() + tdir[2:]

    print(f"\n--- {label} ---")
    print(f"Docker path: {tdir}")

    cnt = client.containers.run(
        'python:3.10-slim',
        f'python /code/{os.path.basename(tf)}',
        volumes={tdir: {'bind': '/code', 'mode': 'ro'}},
        remove=False, detach=True,
    )
    exit_status = cnt.wait(timeout=15)
    stdout_bytes = cnt.logs(stdout=True, stderr=False)
    stderr_bytes = cnt.logs(stdout=False, stderr=True)
    cnt.remove(force=True)
    os.unlink(tf)

    print(f"Exit status: {exit_status}")
    print(f"stdout bytes: {repr(stdout_bytes[:200])}")
    print(f"stderr bytes: {repr(stderr_bytes[:200])}")
    decoded = stdout_bytes.decode('utf-8', errors='replace')
    print(f"stdout decoded: {repr(decoded)}")

import paramiko, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
creds = {}
with open(env_path) as f:
    for line in f:
        m = re.match(r'^(SERVER|PASSWORD)\s*[=:]\s*(.+)', line.strip())
        if m:
            creds[m.group(1)] = m.group(2).strip()

HOST = creds.get("SERVER", "178.156.134.29")
PASS = creds.get("PASSWORD", "")
CONTAINER = "paperclip_paperclip.1.cy4s82a683bdlxc9zsqzpm0j8"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username="root", password=PASS, timeout=15)

def run(cmd, timeout=20):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    return out, err

# Ver logs recentes relacionados ao request_confirmation e claude-login
print("=== Logs: request_confirmation / claude-login ===")
out, _ = run(f"docker logs {CONTAINER} 2>&1 | grep -i 'request_confirmation\\|claude-login\\|clear-error\\|clear_error\\|MOFAA-33\\|assertBoard\\|board' | tail -30")
print(out or "nenhum log encontrado")

# Ver logs do issue MOFAA-33
print("\n=== Logs: MOFAA-33 ===")
out, _ = run(f"docker logs {CONTAINER} 2>&1 | grep -i 'MOFAA-33\\|8a680348' | tail -20")
print(out or "nenhum log")

# Ver últimas mensagens no thread do issue
print("\n=== Logs últimos 50 ===")
out, _ = run(f"docker logs {CONTAINER} 2>&1 | tail -50")
print(out)

client.close()

import os,sys,glob,time,re
import paramiko

to_transfer = 'Glow_salt_001/'

def run_command(cmd, prompt_regex=r'[$#] ', timeout=5, verbose=True):
    shell.send(cmd + "\n")
    buffer = ""
    start = time.time()

    if timeout == -1:
        time.sleep(1)
        # Continuous read mode
        timeout2 = 60  # seconds of inactivity before stopping
        last_data_time = time.time()
        while True:
            if shell.recv_ready():
                data = shell.recv(4096).decode(errors="ignore")
                buffer += data
                last_data_time = time.time()
                if verbose and data.strip():
                    print(data, end="", flush=True)
            else:
                if time.time() - last_data_time > timeout2:
                    if verbose:
                        print(f"\n[No data for {timeout2}s, stopping read]\n")
                    break
            time.sleep(0.1)
    else:
        # Normal mode with timeout and prompt detection
        while True:
            if shell.recv_ready():
                data = shell.recv(4096).decode(errors="ignore")
                buffer += data
                if verbose and data.strip():
                    print(data, end="", flush=True)
                if re.search(prompt_regex, buffer):
                    break
            if time.time() - start > timeout:
                break
            time.sleep(0.1)

    return buffer

ssh_details_path = os.path.normpath(r'server_functions\server_details.txt')

ssh_details = {}
with open(ssh_details_path) as f:
    for line in f:
       (key, val) = line.split(maxsplit=1)
       ssh_details[key] = val.rstrip()
del key, val

print(ssh_details_path)
print(ssh_details)

ssh_client = paramiko.SSHClient()
ssh_client.load_system_host_keys()
# ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(ssh_details['path'], username=ssh_details['username'], password=ssh_details['password'])

print('Conecting to ssh shell')
shell = ssh_client.invoke_shell()
time.sleep(2)  # wait for command execution

response = run_command('cd /')
response = run_command('pwd')
response = run_command('cd ' + ssh_details['cd_path'])
response = run_command('pwd')
response = run_command('ls')

time.sleep(1)

response = run_command('scp -r ' + '"' + to_transfer + '" ' + ssh_details['scp_path'])
time.sleep(1)
response = run_command('to the place where i belong',timeout=15)
time.sleep(1)
response = run_command('1',timeout=-1)
time.sleep(1)

# ssh_stdin, ssh_stdout, ssh_stderr = ssh_client.exec_command('pwd')
# for line in ssh_stdout.readlines():
#     print(line)
ssh_client.close()


print('EOF')
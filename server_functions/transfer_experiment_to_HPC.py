import os,sys,glob,time,re
from natsort import natsorted
import paramiko

# this is the data to transfer over to the HPC
to_transfer = 'Fluorescent_markers_001/'

# this is the path to the txt file containing all the information
ssh_details_path = os.path.normpath(r'server_functions\server_details.txt')

# this is to sanitize the ssh outputs
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def run_command(cmd, prompt_regex=r'[$#] ', timeout=5, verbose=True,wait_time = 2, timeout2 = 60):
    print('SENDING:' + cmd)
    shell.send(cmd + "\n")
    buffer = ""
    start = time.time()

    if timeout == -1:
        time.sleep(1)
        # Continuous read mode
        # timeout2 = timeout2  # seconds of inactivity before stopping
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
            # sleep time to make sure commands are processed 
        time.sleep(wait_time)
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

ssh_details = {}
with open(ssh_details_path) as f:
    for line in f:
       (key, val) = line.split(maxsplit=1)
       ssh_details[key] = val.rstrip()
del key, val
5
print(ssh_details_path)
print(ssh_details)

ssh_client = paramiko.SSHClient()
ssh_client.load_system_host_keys()
# ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(ssh_details['NAS_path'], username=ssh_details['NAS_username'], password=ssh_details['NAS_password'])

print('Conecting to ssh shell')
shell = ssh_client.invoke_shell()
time.sleep(2)  # wait for command execution
response = run_command('')
time.sleep(2)

response = run_command('cd /')
response = run_command('pwd')
response = run_command('cd ' + ssh_details['cd_path'])
response = run_command('pwd')
response = run_command('ls',verbose=False)

found_files = ansi_escape.sub('', response).split('\r\n')
found_folders = []
for this_file in found_files:
    if '.' not in this_file:
        if this_file[0] == ' ':
            this_file = this_file[1:]
        if len(this_file) > 2:
            found_folders.append(this_file)
found_folders = natsorted(found_folders)

if to_transfer.strip('/') not in found_folders:
    print('Specified folder not found--->',to_transfer)
    print('EXITING')
    ssh_client.close()
    sys.exit()

time.sleep(1)

response = run_command('scp -r ' + '"' + to_transfer + '" ' + ssh_details['scp_path'])
time.sleep(1)
response = run_command(ssh_details['HPC_password'],timeout=-1, timeout2=15)
time.sleep(1)
response = run_command('1',timeout=-1, timeout2=60)
time.sleep(1)


ssh_client.close()


print('EOF')
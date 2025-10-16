
import pexpect
import time
import datetime
import sys
import subprocess
import queue
import threading


# Released under MIT License
# Copyright (c) 2025 StarkGtsk.

class TonStorageAPI:
    def __init__(self, startup_cmd: str):
        self.startup_cmd = startup_cmd
        self.child = None
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        self.output_buffer = ""
        self.current_command_output = ""

    def check_daemon_alive(self) -> bool:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "storage-daemon"],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except:
            return False

    def _collect_output(self):
        """Collect output from CLI and store for current command"""
        while self.is_running and self.child and self.child.isalive():
            try:
                char = self.child.read(1)
                if char:
                    self.output_buffer += char
                    self.current_command_output += char
                    sys.stdout.write(char)
                    sys.stdout.flush()
            except:
                break

    def start_cli_session(self) -> bool:
        if not self.check_daemon_alive():
            print(f'[{datetime.datetime.now()}] ERROR: STORAGE-DAEMON IS NOT RUNNING')
            return False

        try:
            self.child = pexpect.spawn(self.startup_cmd, encoding='utf-8', timeout=10)

            # Init collect output in another thread
            self.output_collector = threading.Thread(target=self._collect_output, daemon=True)

            self.is_running = True
            self.output_collector.start()

            # Wait for initialization
            time.sleep(2)

            if not self.child.isalive():
                return False

            print(f'[{datetime.datetime.now()}] LOG: STORAGE-CLI SESSION STARTED')

            # Init command handler
            self.worker_thread = threading.Thread(target=self._command_worker, daemon=True)
            self.worker_thread.start()

            return True

        except Exception as e:
            print(f'[{datetime.datetime.now()}] ERROR: {e}')
            return False

    def _command_worker(self):
        while self.is_running:
            try:
                command_data = self.command_queue.get(timeout=1.0)
                command_id, command, callback = command_data

                # Reset output buffer for new command
                self.current_command_output = ""

                # Send command to CLI
                self.child.sendline(command)

                # Wait for command execution
                time.sleep(self._get_command_timeout(command))

                # Get the command output (everything after the command was sent)
                command_output = self._extract_command_output(command)

                # Prepare response with both status and actual output
                response = {
                    'status': f'[{datetime.datetime.now()}] LOG: COMMAND {command} EXECUTED',
                    'output': command_output
                }

                if callback:
                    callback(command_id, response)

                self.response_queue.put((command_id, response))

            except queue.Empty:
                continue
            except Exception as e:
                error_response = {
                    'status': f'[{datetime.datetime.now()}] ERROR: {e}',
                    'output': ''
                }
                self.response_queue.put(("ERROR", error_response))

    def _extract_command_output(self, command: str) -> str:
        """Extract clean output for the specific command"""
        if not self.current_command_output:
            return ""

        # Remove the command echo and get only the response
        lines = self.current_command_output.split('\n')
        output_lines = []

        # Skip the line with our command and collect everything after
        skip_next = False
        for line in lines:
            if command in line:
                skip_next = True
                continue
            if skip_next:
                # Skip empty lines immediately after command
                if line.strip():
                    output_lines.append(line)
                skip_next = False
            elif line.strip() and not line.startswith('[') and 'ERROR' not in line:
                output_lines.append(line)

        return '\n'.join(output_lines).strip()

    def _get_command_timeout(self, command: str) -> float:
        if any(cmd in command for cmd in ['list', 'get-peers', 'get-pieces-info']):
            return 3.0
        elif 'create' in command:
            return 4.0
        else:
            return 2.0

    def send_command(self, command: str, command_id: str = None, callback: callable = None):
        if not self.is_running:
            raise RuntimeError(f'[{datetime.datetime.now()}] ERROR: CLI SESSION IS NOT RUNNING')

        if command_id is None:
            command_id = str(datetime.datetime.now().timestamp())

        self.command_queue.put((command_id, command, callback))

        try:
            response_id, response = self.response_queue.get(timeout=10.0)
            if response_id == command_id:
                return response
        except queue.Empty:
            return {
                'status': f'[{datetime.datetime.now()}] ERROR: TIMEOUT WAITING FOR RESPONSE',
                'output': ''
            }

        return {
            'status': f'[{datetime.datetime.now()}] ERROR: UNKNOWN RESPONSE',
            'output': ''
        }

    # All your existing methods (create, add_by_hash, etc.) remain the same
    # but they will now return dictionaries with 'status' and 'output' keys

    def create(self, path: str, description: str = None, no_upload: bool = False, copy: bool = False,
               json_output: bool = False):
        cmd = f"create {path}"
        if description:
            cmd += f" -d {description}"
        if no_upload:
            cmd += f" --no-upload"
        if copy:
            cmd += f" --copy"
        if json_output:
            cmd += f" --json"
        return self.send_command(cmd)

    def add_by_hash(self, bag_id: str, root_dir: str = None, paused: bool = False, no_upload: bool = False,
                    json_output: bool = False, partial: list = None):
        cmd = f"add-by-hash {bag_id}"
        if root_dir:
            cmd += f" -d {root_dir}"
        if paused:
            cmd += f" --paused"
        if no_upload:
            cmd += f" --no-upload"
        if json_output:
            cmd += f" --json"
        if partial:
            cmd += " --partial " + " ".join(partial)
        return self.send_command(cmd)

    def list_bags(self, hashes: bool = False, json_output: bool = False):
        cmd = "list"
        if hashes:
            cmd += " --hashes"
        if json_output:
            cmd += " --json"
        return self.send_command(cmd)

    def get_bag_info(self, bag: str, json_output: bool = False):
        cmd = f"get {bag}"
        if json_output:
            cmd += " --json"
        return self.send_command(cmd)

    def help(self):
        return self.send_command("help")

    def deploy_provider(self):
        return self.send_command("deploy-provider")

    def stop(self):
        self.is_running = False
        if self.child and self.child.isalive():
            self.child.sendline("exit")
            self.child.close()
        print(f'[{datetime.datetime.now()}] LOG: STORAGE-CLI SESSION STOPPED')

    def run_interactive_storage_cli(self):
        try:

            child = pexpect.spawn(self.startup_cmd, encoding='utf-8', timeout=10)
            child.logfile = sys.stdout
            child.expect(pexpect.EOF, timeout=1)


        except pexpect.TIMEOUT:
            while True:
                try:
                    child.expect(pexpect.EOF, timeout=1)
                except pexpect.TIMEOUT:
                    print(f'[{datetime.datetime.now()}] LOG: STORAGE-DAEMON-CLI IS WORKING')
                    uinput = input(">>> ")
                    if uinput.lower() in ['exit', 'close', 'quit']:
                        print(f'[{datetime.datetime.now()}] LOG: STORAGE-DAEMON-CLI STOP')

                        child.sendline("exit")
                    if not child.isalive():
                        print(f'[{datetime.datetime.now()}] ERROR: PROCESS UNEXPECTEDLY STOPPED')
                        break
                    else:
                        child.sendline(uinput)
                except Exception as e:
                    print(f'[{datetime.datetime.now()}] ERROR: {e}')


if __name__ == "__main__":
    storage_cli_startup = '/Users/gtsk/ton/build/storage/storage-daemon/storage-daemon-cli -I 127.0.0.1:5555 -k /Users/gtsk/ton/build/storage/storage-daemon/ton-storage-db/cli-keys/client -p /Users/gtsk/ton/build/storage/storage-daemon/ton-storage-db/cli-keys/server.pub'

    api = TonStorageAPI(storage_cli_startup)

    if api.start_cli_session():
        print(api.help())
        time.sleep(3)
        print(api.help())
        time.sleep(2)
        print(api.deploy_provider())
        api.stop()

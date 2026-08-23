import time
import requests
import json

class CySiemReceiver:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.server_url = self.config['server_url']
        self.agent_id = self.config['agent_id']

    def check_commands(self):
        # Poll server for any pending commands/playbooks
        url = f"{self.server_url}/api/agents/{self.agent_id}/commands"
        try:
            # response = requests.get(url)
            # if response.status_code == 200:
            #     execute_command(response.json())
            pass
        except:
            pass

    def run(self):
        print(f"Starting CySIEM Command Receiver for Agent {self.agent_id}...")
        while True:
            self.check_commands()
            time.sleep(10)

if __name__ == "__main__":
    receiver = CySiemReceiver()
    receiver.run()

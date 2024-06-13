import requests

class ZeroTierClient:
    def __init__(self, api_token):
        self.api_token = api_token
        self.base_url = "https://api.zerotier.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}"
        }

    def list_networks(self):
        url = f"{self.base_url}/network"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_network_details(self, network_id):
        url = f"{self.base_url}/network/{network_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def list_members(self, network_id):
        url = f"{self.base_url}/network/{network_id}/member"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def authorize_member(self, network_id, member_id, authorize=True):
        url = f"{self.base_url}/network/{network_id}/member/{member_id}"
        data = {
            "config": {
                "authorized": authorize
            }
        }
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_network(self, network_id, data):
        url = f"{self.base_url}/network/{network_id}"
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def update_member_ip(self, network_id, member_id, new_ip):
        url = f"{self.base_url}/network/{network_id}/member/{member_id}"
        data = {
            "config": {
                "ipAssignments": [new_ip]
            }
        }
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def create_network(self, name, description="", private=True):
        url = f"{self.base_url}/network"
        data = {
            "config": {
                "name": name,
                "description": description,
                "private": private
            }
        }
        response = requests.post(url, json=data, headers=self.headers)
        response.raise_for_status()
        return response.json()

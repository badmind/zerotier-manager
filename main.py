import sys
import traceback
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QListWidget, QListWidgetItem, QLineEdit, QHBoxLayout, QFormLayout, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt
import winreg
from zerotier_client import ZeroTierClient
from edit_network_dialog import EditNetworkDialog

def get_api_key():
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ZeroTier", 0, winreg.KEY_READ)
        api_key, _ = winreg.QueryValueEx(registry_key, "ApiKey")
        winreg.CloseKey(registry_key)
        return api_key
    except WindowsError:
        return None

class NewNetworkDialog(QDialog):
    def __init__(self, client, parent=None):
        super(NewNetworkDialog, self).__init__(parent)
        self.client = client
        self.parent_widget = parent
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Create a New Network')
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        form_layout.addRow('Name:', self.name_input)

        self.description_input = QLineEdit()
        form_layout.addRow('Description:', self.description_input)

        self.private_input = QLineEdit('True')
        form_layout.addRow('Private:', self.private_input)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

    def accept(self):
        name = self.name_input.text()
        description = self.description_input.text()
        private = self.private_input.text().lower() == 'true'

        try:
            new_network = self.client.create_network(name, description, private)
            self.parent_widget.loadNetworks()
            self.parent_widget.selectNetwork(new_network['id'])
            super().accept()
        except Exception as e:
            print(f"Error creating network: {e}")
            traceback.print_exc()

class ZeroTierGUI(QWidget):
    def __init__(self, api_token):
        super().__init__()
        self.client = ZeroTierClient(api_token)
        self.initUI()

    def initUI(self):
        self.setWindowTitle('ZeroTier Manager')
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()

        self.networkList = QListWidget()
        self.networkList.itemClicked.connect(self.onNetworkClicked)
        layout.addWidget(self.networkList)

        self.networkDetails = QLabel("Select a network to view details")
        layout.addWidget(self.networkDetails)

        self.memberList = QListWidget()
        self.memberList.itemClicked.connect(self.onMemberClicked)
        layout.addWidget(self.memberList)

        self.authButton = QPushButton('Authorize/Deauthorize Selected Member')
        self.authButton.clicked.connect(self.toggleMemberAuthorization)
        layout.addWidget(self.authButton)

        self.editNetworkButton = QPushButton('Edit Network')
        self.editNetworkButton.clicked.connect(self.editSelectedNetwork)
        layout.addWidget(self.editNetworkButton)

        self.newNetworkButton = QPushButton('Create New Network')
        self.newNetworkButton.clicked.connect(self.createNewNetwork)
        layout.addWidget(self.newNetworkButton)

        self.ipEdit = QLineEdit()
        self.ipEdit.setPlaceholderText("Enter new IP address for selected member")
        layout.addWidget(self.ipEdit)

        self.ipButton = QPushButton('Update IP Address of Selected Member')
        self.ipButton.clicked.connect(self.updateMemberIP)
        layout.addWidget(self.ipButton)

        self.refreshButton = QPushButton('Refresh Network Details')
        self.refreshButton.clicked.connect(self.refreshNetworkDetails)
        layout.addWidget(self.refreshButton)

        self.statusLabel = QLabel('Status: Ready')
        layout.addWidget(self.statusLabel)

        self.setLayout(layout)
        self.loadNetworks()

    def loadNetworks(self):
        try:
            networks = self.client.list_networks()
            self.networkList.clear()
            for network in networks:
                item = QListWidgetItem(f"{network.get('config', {}).get('name', 'Unnamed')} ({network['id']})")
                item.setData(Qt.UserRole, network['id'])
                self.networkList.addItem(item)
        except Exception as e:
            self.statusLabel.setText(f"Error loading networks: {e}")
            print(f"Error loading networks: {e}")
            traceback.print_exc()

    def selectNetwork(self, network_id):
        items = self.networkList.findItems(network_id, Qt.MatchContains)
        if items:
            self.networkList.setCurrentItem(items[0])
            self.onNetworkClicked(items[0])

    def onNetworkClicked(self, item):
        network_id = item.data(Qt.UserRole)
        self.networkDetails.clear()
        self.memberList.clear()
        self.current_network_id = network_id
        self.loadNetworkDetails(network_id)

    def loadNetworkDetails(self, network_id):
        try:
            network_details = self.client.get_network_details(network_id)
            network_info = (f"ID: {network_details['id']}\n"
                            f"Name: {network_details.get('config', {}).get('name', 'N/A')}\n"
                            f"Description: {network_details.get('config', {}).get('description', 'N/A')}\n"
                            f"Private: {network_details.get('config', {}).get('private', 'N/A')}\n"
                            f"Subnet: {self.format_ip_pools(network_details.get('config', {}).get('ipAssignmentPools', []))}\n"
                            f"Nodes: {len(self.client.list_members(network_id))}\n"
                            f"Created: {network_details.get('creationTime', 'N/A')}")
            self.networkDetails.setText(network_info)

            members = self.client.list_members(network_id)
            for member in members:
                member_item = QListWidgetItem(f"ID: {member['nodeId']} - Authorized: {member['config']['authorized']} - Physical IP: {member.get('physicalAddress', 'N/A')}")
                member_item.setData(Qt.UserRole, (network_id, member['nodeId'], member['config']['authorized'], member['config'].get('ipAssignments', [])))
                self.memberList.addItem(member_item)
        except Exception as e:
            self.statusLabel.setText(f"Error loading network details: {e}")
            print(f"Error loading network details: {e}")
            traceback.print_exc()

    def format_ip_pools(self, pools):
        return ', '.join([f"{pool['ipRangeStart']}-{pool['ipRangeEnd']}" for pool in pools])

    def onMemberClicked(self, item):
        network_id, member_id, authorized, ip_assignments = item.data(Qt.UserRole)
        if ip_assignments:
            self.ipEdit.setText(ip_assignments[0])
        else:
            self.ipEdit.clear()

    def toggleMemberAuthorization(self):
        selectedРазбирам, нека поправим и завършим кода.

### Обновен `zerotier_client.py`

```python
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

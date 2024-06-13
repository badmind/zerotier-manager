from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox

class EditNetworkDialog(QDialog):
    def __init__(self, network_details, client, parent=None):
        super(EditNetworkDialog, self).__init__(parent)
        self.client = client
        self.network_id = network_details['id']
        self.initUI(network_details)

    def initUI(self, network_details):
        self.setWindowTitle('Edit Network')
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_input = QLineEdit(network_details.get('config', {}).get('name', ''))
        form_layout.addRow('Name:', self.name_input)

        self.description_input = QLineEdit(network_details.get('config', {}).get('description', ''))
        form_layout.addRow('Description:', self.description_input)

        self.private_input = QLineEdit(str(network_details.get('config', {}).get('private', '')))
        form_layout.addRow('Private:', self.private_input)

        self.v4assignments_input = QLineEdit(self.format_ip_pools(network_details.get('config', {}).get('ipAssignmentPools', [])))
        form_layout.addRow('IPv4 Assignment Pools:', self.v4assignments_input)

        self.v6assignments_input = QLineEdit(str(network_details.get('config', {}).get('v6AssignMode', '')))
        form_layout.addRow('IPv6 Assignment Mode:', self.v6assignments_input)

        self.multicast_input = QLineEdit(str(network_details.get('config', {}).get('multicastLimit', '')))
        form_layout.addRow('Multicast Limit:', self.multicast_input)

        self.dns_input = QLineEdit(network_details.get('config', {}).get('dns', {}).get('domain', ''))
        form_layout.addRow('DNS Domain:', self.dns_input)

        self.dns_server_input = QLineEdit(', '.join(network_details.get('config', {}).get('dns', {}).get('servers', [])))
        form_layout.addRow('DNS Servers:', self.dns_server_input)

        layout.addLayout(form_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

        self.setLayout(layout)

    def format_ip_pools(self, pools):
        return ', '.join([f"{pool['ipRangeStart']}-{pool['ipRangeEnd']}" for pool in pools])

    def parse_ip_pools(self, text):
        pools = []
        for pool in text.split(','):
            start, end = pool.split('-')
            pools.append({"ipRangeStart": start.strip(), "ipRangeEnd": end.strip()})
        return pools

    def accept(self):
        data = {
            'config': {
                'name': self.name_input.text(),
                'description': self.description_input.text(),
                'private': self.private_input.text().lower() == 'true',
                'ipAssignmentPools': self.parse_ip_pools(self.v4assignments_input.text()),
                'v6AssignMode': self.v6assignments_input.text(),
                'multicastLimit': self.multicast_input.text(),
                'dns': {
                    'domain': self.dns_input.text(),
                    'servers': [s.strip() for s in self.dns_server_input.text().split(',')]
                }
            }
        }
        self.client.update_network(self.network_id, data)
        super().accept()

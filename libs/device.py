from configparser import ConfigParser, NoOptionError

from libs.grist import Grist


def device_inventory(config: ConfigParser, grist: Grist, account: dict, data: dict):
	"""
	Process device inventory data for a given account.

	:param config: System configuration settings, loaded from config.ini
	:param grist: An instance of the Grist class for database operations.
	:param account: A dictionary representing the account information.
	:param data: A dictionary containing device inventory data.
	:return: A string indicating the result of the operation.
	"""

	if 'mac_primary' not in data and 'mac_secondary' not in data:
		return 400, 'No MAC address provided', None

	# List of fields which should not trigger a change note
	silent_keys = list(map(str.strip, config.get('devices', '_silent').split(',')))

	# Allow "weak" data to be passed in; these keys will be values which should not overwrite existing data.
	if '_weak' in data:
		weak_keys = data['_weak']
		del data['_weak']
	else:
		weak_keys = []

	# Override a few fields on the incoming data
	data['status'] = 'Active'
	data['account'] = account['id']

	# Assemble the payload to send to the spreadsheet
	fields = {}
	log = ''
	message = ''

	# Find the device under the given account with one of the MAC addresses as either its primary or secondary.
	id = None
	macs = []
	if 'mac_primary' in data:
		macs.append(data['mac_primary'])
	if 'mac_secondary' in data:
		macs.append(data['mac_secondary'])

	device = grist.get('Devices', filter={
		config.get('devices', 'account'): [account['id']],
		config.get('devices', 'mac_primary'): macs,
	}, limit=1)
	if device:
		id = device['id']
	else:
		device = grist.get('Devices', filter={
			config.get('devices', 'account'): [account['id']],
			config.get('devices', 'mac_secondary'): macs,
		}, limit=1)
		if device:
			id = device['id']

	if device:
		# Allow MAC and IP addresses to change between primary and secondary, based on the sheet.
		# This is because a scan may retrieve a wired NIC and WIFI card and log them both as primary.
		if ('mac_primary' in data and
			config.get('devices', 'mac_secondary') in device['fields'] and
			data['mac_primary'] == device['fields'][config.get('devices', 'mac_secondary')]
		):
			if 'mac_secondary' in data:
				m = data['mac_secondary']
				data['mac_secondary'] = data['mac_primary']
				data['mac_primary'] = m
			else:
				data['mac_secondary'] = data['mac_primary']
				del data['mac_primary']

			if 'ip_secondary' in data:
				m = data['ip_secondary']
				data['ip_secondary'] = data['ip_primary']
				data['ip_primary'] = m
			else:
				data['ip_secondary'] = data['ip_primary']
				del data['ip_primary']
		elif ('mac_secondary' in data and
		      config.get('devices', 'mac_primary') in device['fields'] and
		      data['mac_secondary'] == device['fields'][config.get('devices', 'mac_primary')]
		):
			if 'mac_primary' in data:
				m = data['mac_primary']
				data['mac_primary'] = data['mac_secondary']
				data['mac_primary'] = m
			else:
				data['mac_primary'] = data['mac_secondary']
				del data['mac_secondary']

			if 'ip_primary' in data:
				m = data['ip_primary']
				data['ip_primary'] = data['ip_secondary']
				data['ip_secondary'] = m
			else:
				data['ip_primary'] = data['ip_secondary']
				del data['ip_secondary']

	if device:
		# Device exists, selectively update changed records and keep a tally of changes.
		changes = []
		for k, v in data.items():
			try:
				db_k = config.get('devices', k)
				if db_k == '':
					db_k = None
			except NoOptionError:
				db_k = None

			if db_k is None:
				# Destination column does not exist, (or at least is not mapped)
				continue

			if v is None:
				# No value provided, skip it.
				continue

			if db_k not in device['fields']:
				# Target column does not exist in the sheet!
				continue

			if k in weak_keys and device['fields'][db_k] not in (None, ''):
				# Weak key provided, and existing value is not empty; skip it.
				continue

			if device['fields'][db_k] != v:
				if k not in silent_keys:
					changes.append(f"{db_k} changed from [{device['fields'][db_k]}] to [{v}]")
				fields[db_k] = v

		if len(changes) > 0:
			message = 'Changed applied to existing device'
			log = 'Detected changes from inventory update:\n\n* ' + '\n* '.join(changes)
		else:
			message = 'No changes detected'

		if len(fields) > 0:
			grist.update(config.get('devices', '_table'), id, fields)
	else:
		message = 'New device added to inventory'
		log = 'New device added from inventory update.'
		for k, v in data.items():
			try:
				db_k = config.get('devices', k)
				if db_k == '':
					db_k = None
			except NoOptionError:
				db_k = None

			if db_k is not None and v is not None:
				fields[db_k] = v

		id = grist.add(config.get('devices', '_table'), fields)

	# Create a note entry of the changes
	if log:
		log_data = {
			config.get('notes', 'device'): id,
			config.get('notes', 'note'): log,
		}
		grist.add(config.get('notes', '_table'), log_data)
	return 200, message, {'id': id}

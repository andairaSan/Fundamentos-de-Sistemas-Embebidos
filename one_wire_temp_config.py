import os

class one_wire_temp_config:

	def __init__(self,prefix ='28'):
		self.base_dir = '/sys/bus/w1/devices/'
		self.prefix = prefix
		self.device_file = None
		self._config_device()
	#end def

	def _config_device(self):
		try:
			if os.path.exists(self.base_dir):
				devices = [d for d in os.listdir(self.base_dir) \
					if d.startswith(self.prefix)]
			if devices:
				device_folder = os.path.join(self.base_dir, devices[0])
				self.device_file = os.path.join(device_folder, 'w1_slave')
		
		except Exception:
			self.device_file = None
	#end def
	def read_temp(self):
		if not self.device_file:
			self._config_device()
		if not self.device_file:
			return None #we have nothinf connected!
	
		try:
			with open(self.device_file, 'r') as f:
				lines = f.readlines()
			full_text = "".join(lines)
			if 'YES' not in lines[0]:
				return None #Error on protocol read
			
			position_t = full_text.find('t=')
			if position_t != -1:
				string_value = full_text[position_t +2:].strip()
				return float(string_value)/1000

		except Exception as e:
			print(f"Internal Error in class: {e}",e)
			return None
		return None

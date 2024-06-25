class E4MameManager:
	"""
	Class that manages both games and favorites instance of E4Mame.
	"""
	
	def __init__(self):
		self.instances = {}
	
	def add_instance(self, name, instance):
		"""
		Add an instance to the manager.
		
		:param name: The name of the instance.
		:param instance: The instance to add.
		"""
		self.instances[name] = instance
		
	def get_instance(self, name):
		"""
		Get an instance from the manager or None.
		
		:param name: The name of the instance.
		"""
		return self.instances.get(name, None)

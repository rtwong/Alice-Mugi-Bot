class RpgCharacter:
	def __init__(self, id, exp=0, weapon=0, armour=0, _str=0, _int=0, _dex=0):
		self.id = id
		self.exp = exp
		self.weapon = weapon
		self.armour = armour
		self._str = _str
		self._int = _int
		self._dex = _dex

	def set_id(self, id):
		self.id = id
	def get_id(self):
		return self.id

	def set_exp(self, exp):
		self.exp = exp
	def get_exp(self):
		return self.exp

	def set_weapon(self, weapon):
		self.weapon = weapon
	def get_weapon(self):
		return self.weapon

	def set_armour(self, armour):
		self.armour = armour
	def get_armour(self):
		return self.armour

	def set_str(self, _str):
		self._str = _str
	def get_str(self):
		return self._str

	def set_int(self, _int):
		self._int = _int
	def get_int(self):
		return self._int

	def set_dex(self, _dex):
		self._dex = _dex
	def get_dex(self):
		return self._dex

class Weapon:
	def __init__(self, )
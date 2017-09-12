import random

class Card:
	def __init__(self, value, suit):
		self.value = value
		self.suit = suit

class Deck:
	def __init__(self, num_decks=1):
		suits =["Diamonds", "Clubs", "Hearts", "Spades"]
		values = ["Ace","2","3","4","5","6","7","8","9","10","Jack","Queen","King"]
		self.deck = []

		for i in range(num_decks):
			for suit in suits:
				for value in values:
					self.deck.append(Card(value,suit))

	def card_shuffle(self):
		random.shuffle(self.deck)

	def draw(self):
		self.card_shuffle()
		return self.deck.pop()

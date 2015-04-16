import unittest
from app.models import User
import time
from app import create_app, db
from datetime import datetime 

class UserModelTestCase(unittest.TestCase):
	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
		self.app_context.pop()


	def test_password_setter(self):
		u = User(password='cat')
		self.assertTrue(u.password_hash is not None)

	def test_no_password_getter(self):
		u = User(password='cat')
		with self.assertRaises(AttributeError):
			u.password

	def test_password_verification(self):
		u = User(password='cat')
		self.assertTrue(u.verify_password('cat'))
		self.assertFalse(u.verify_password('dog'))

	def test_password_salts_are_random(self):
		u = User(password='cat')
		u2 = User(password='cat')
		self.assertTrue(u.password_hash != u2.password_hash)

	def test_valid_confirmation_token(self):
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		token = u.generate_confirmation_token()
		self.assertTrue(u.confirm(token))

	def test_invalid_confirmation_token(self):
		u1 = User(password='cat')
		u2 =  User(password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		token = u1.generate_confirmation_token()
		self.assertFalse(u2.confirm(token))

	def test_expired_confirmation_token(self):
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		token = u.generate_confirmation_token(1)
		time.sleep(2)
		self.assertFalse(u.confirm(token))

	def test_valid_reset_token(self):
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		token = u.generate_reset_token()
		self.assertTrue(u.reset_password(token, 'dog'))
		self.assertTrue(u.verify_password('dog'))

	def test_invalid_reset_token(self):
		u1 = User(password='cat')
		u2 =  User(password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		token = u1.generate_reset_token()
		self.assertFalse(u2.reset_password(token, 'horse'))
		self.assertTrue(u2.verify_password('dog'))

	def test_valid_email_change_token(self):
		u = User(email='joe@example.com', password='cat')
		db.session.add(u)
		db.session.commit()
		token = u.generate_email_change_token('jim@example.com')
		self.assertTrue(u.change_email(token))
		self.assertTrue(u.email == 'jim@example.com')

	def test_invalid_email_change_token(self):
		u1 = User(email='joe1@example.org', password='cat')
		u2 = User(email='jim1@example.org', password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		token = u1.generate_email_change_token('dave@example.org')
		self.assertFalse(u2.change_email(token))
		self.assertTrue(u2.email == 'jim1@example.org')


	def test_duplicate_email_change_token(self):
		u1 = User(email='joe@example.org', password='cat')
		u2 = User(email='jim@example.org', password='dog')
		db.session.add(u1)
		db.session.add(u2)
		db.session.commit()
		token = u2.generate_email_change_token('joe@example.com')
		self.assertFalse(u2.change_email(token))
		self.assertTrue(u2.email == 'jim@exmaple.com')


	def test_roles_and_permissions(self):
		Role.insert_roles()
		u = User(email='john@example.com', password='cat')
		self.assertTrue(u.can(Permission.WRITE_ARTICLES))
		self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

	def test_ananymous_user(self):
		u = AnonymousUser()
		self.assertFalse(u.can(Permission.FOLLOW))

	def test_timestamp:
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		self.assertTrue((datetime.utcnow() - u.member_since).total_seconds() < 3)
		self.assertTrue((datetime.utcnow() - u.last_seen).total_seconds() < 3)

	def test_ping(self):
		u = User(password='cat')
		db.session.add(u)
		db.session.commit()
		time.sleep(2)
		last_seen_before = u.last_seen
		u.ping()
		self.assertTrue(u.last_seen > last_seen_before)

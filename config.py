from key import secret_key as key, mail_pass
import os



basedir = os.path.abspath(os.path.dirname(__file__))




class Config:

	CSRF_ENABLED = True 
	SECRET_KEY = os.environ.get('SECRET_KEY') or key 
	SQLALCHEMY_COMMIT_ON_TEARDOWN = True 
	MAIL_SUBJECT_PREFIX = '[718Digital]'
	MAIL_SENDER = 'joeknows718@gmail.com'
	MAIL_SERVER = 'smtp.googlemail.com'
	MAIL_PORT = 587 #465
	MAIL_USE_TLS = True
	#MAIL_USE_SSL = True  
	MAIL_USERNAME = 'joeknows718@gmail.com'#os.environ.get('MAIL_USERNAME')
	MAIL_PASSWORD = mail_pass #os.environ.get('MAIL_PASSWORD')
	ADMIN = "joeknows718@gmail.com"
	@staticmethod
	def init_app(app):
		pass 

class DevelopmentConfig(Config):
	DEBUG = True 
	SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
	TESTING = True 
	SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
	'development': DevelopmentConfig,
	'testing': TestingConfig,
	'production': ProductionConfig,

	'default':DevelopmentConfig
}

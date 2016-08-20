#!/usr/bin/env python
import os
import sys

import dotenv

dotenv.read_dotenv()

if __name__ == "__main__":
	ENVIRONMENT = os.getenv('ENVIRONMENT')

	if ENVIRONMENT == 'STAGING':
		settings = 'staging'
	elif ENVIRONMENT == 'PRODUCTION':
		settings = 'local'
	else:
		settings = 'development'
		
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tienda.settings")

	from django.core.management import execute_from_command_line

	execute_from_command_line(sys.argv)

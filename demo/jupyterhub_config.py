import os
from traitlets import config

c = config.get_config()

# Register the papermillhub service with JupyterHub
c.JupyterHub.services = [
    {
        "name": "papermillhub",
        "admin": True,
        "url": "http://127.0.0.1:21211",
        "command": ["papermillhub"],
    }
]
c.JupyterHub.service_tokens = {"super-secret": "papermillhub"}

# Setup authenticator and spawners
c.JupyterHub.admin_access = True  # Service needs to access user servers.
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"
c.SimpleLocalProcessSpawner.home_dir_template = os.getcwd()
c.Spawner.default_url = "/lab"

import requests
import json

# The URL for the PapermillHub API endpoint
papermill_url = "http://localhost:8000/services/papermillhub/api/jobs/"
# A token that the PapermillHub service can use to authenticat
# with JupyterHub
papermillhub_token = "super-secret"

# A test username
user = "user"

# Create a user token, which can supsequently be used to invoke
# papermillhub as if the user were launching the job.
note = "Created by PapermillHub"
r = requests.post(
    f"http://127.0.0.1:8081/hub/api/users/{user}/tokens",
    headers={"Authorization": "token %s" % papermillhub_token},
    json={"note": note},
)
r.raise_for_status()
user_token = r.json()["token"]

# Launch the papermillhub job as the user.
r = requests.post(
    papermill_url,
    headers={"Authorization": "token %s" % user_token},
    json=json.dumps({"in_path": "grab_image.ipynb", "out_path": "grabbed_image.ipynb"}),
)
r.raise_for_status()
print(r.json())

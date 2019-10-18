# Demo of papermillhub as a JupyterHub service

This is a minimal demo of how you can use PapermillHub as a JupyterHub service.

## Installation

Install the package and enable the jupyter server extension:
```bash
pip install -e .
jupyter serverextension enable --sys-prefix papermillhub.nbext
```

## Running the demo

1. Launch JupyterHub with the example configuration:
```bash
jupyterhub --config=jupyterhub_config.py
```
1. Go to `http://localhost:8000` in a browser.
1. Log in to JupyterHub using the test username "user".
1. In a separate terminal, trigger a papermill job:
```bash
python trigger.py
```
If you have shut down your server after logging in, this should restart it.
1. You should see a new file `grabbed_image.ipynb`,
which is the output of the papermill job.
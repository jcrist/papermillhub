"""
Launch a user server via JupyterHub

This file has been modified from the Python package binderhub.
"""
import json
import os

from tornado.log import app_log
from tornado import web, gen
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPError


class Launcher:

    retry_delay = 20
    retries = 100
    hub_url = "127.0.0.1:8000/"

    def __init__(self, user, auth):
        self.hub_api_token = auth
        self.user = user

    async def api_request(self, url, *args, **kwargs):
        """Make an API request to JupyterHub"""
        headers = kwargs.setdefault("headers", {})
        headers.update({"Authorization": "token %s" % self.hub_api_token})
        hub_api_url = os.getenv("JUPYTERHUB_API_URL", "") or self.hub_url + "hub/api"
        if not hub_api_url.endswith("/"):
            hub_api_url = hub_api_url + "/"
        request_url = hub_api_url + url
        req = HTTPRequest(request_url, *args, **kwargs)
        retry_delay = self.retry_delay
        for i in range(1, self.retries + 1):
            try:
                return await AsyncHTTPClient().fetch(req)
            except HTTPError as e:
                # swallow 409 errors on retry only (not first attempt)
                if i > 1 and e.code == 409 and e.response:
                    app_log.debug("Treating 409 conflict on retry as success")
                    return e.response
                # retry requests that fail with error codes greater than 500
                # because they are likely intermittent issues in the cluster
                # e.g. 502,504 due to ingress issues or Hub relocating,
                # 599 due to connection issues such as Hub restarting
                if e.code >= 500:
                    app_log.debug(
                        "Error accessing Hub API (using %s): %s", request_url, e
                    )
                    if i == self.retries:
                        # last api request failed, raise the exception
                        raise
                    await gen.sleep(retry_delay)
                    # exponential backoff for consecutive failures
                    retry_delay *= 2
                else:
                    raise

    async def get_user_data(self):
        resp = await self.api_request("users/%s" % self.user["name"], method="GET")
        body = json.loads(resp.body.decode("utf-8"))
        return body

    async def launch(self):
        """
        Launch the user server. At the moment, this just launches the default
        server, with the default args. In the future, we should allow for
        launching named servers with custom spawner args (e.g., custom image
        ids).
        """

        username = self.user["name"]
        # Test if exists and early exit if so
        user_data = await self.get_user_data()
        # The default server is available under the empty string key ""
        started_server = user_data["servers"].get("", None)
        if started_server and started_server["ready"]:
            redirect_url = started_server["url"]
            return {"status": "running", "url": redirect_url}

        # start server
        app_log.debug("Starting server %s for user %s", username)
        try:
            resp = await self.api_request(
                "users/{}/server".format(username), method="POST", body="{}"
            )

            if resp.code == 202:
                # Server hasn't actually started yet
                # We wait for it!
                for i in range(64):
                    user_data = await self.get_user_data()

                    server = user_data["server"]
                    if server["ready"]:
                        # exit, server running
                        return {"status": "running", "url": server["url"]}

                    if server["progress_url"]:
                        # exit, server pending with progress url
                        return {"url": server["progress_url"], "status": "pending"}

                    if not server["pending"]:
                        raise web.HTTPError(
                            500,
                            (
                                "Server for user %s failed to launch"
                                % (username)
                            ),
                        )
                    # FIXME: make this configurable
                    # FIXME: Measure how long it takes for servers to start
                    # and tune this appropriately
                    await gen.sleep(min(1.4 ** i, 10))
                else:
                    raise web.HTTPError(
                        500, ("Server for user %s took too long to launch" % (username))
                    )

        except HTTPError as e:
            if e.response:
                body = e.response.body
            else:
                body = ""

            self.log.error(
                "Error starting server for user {}: {}\n{}".format(username, e, body)
            )
            raise web.HTTPError(500, "Failed to launch server")

        return {"url": "/user/%s" % (username), "status": "running"}

# Copyright (C) 2016 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.
import os
import platform
import pytest
import requests
import sys
import thread

sys.path.insert(0, ".")
import agent

# This whole setup is a bit ugly, but oh well.
thread.start_new_thread(agent.app.run, (), {"port": 0})
while not hasattr(agent.app, "s"):
    continue

class TestAgent(object):
    @property
    def port(self):
        _, port = agent.app.s.socket.getsockname()
        return port

    def get(self, uri, *args, **kwargs):
        return requests.get(
            "http://localhost:%s%s" % (self.port, uri), *args, **kwargs
        )

    def post(self, uri, *args, **kwargs):
        return requests.post(
            "http://localhost:%s%s" % (self.port, uri), *args, **kwargs
        )

    def test_index(self):
        assert self.get("/").json()["message"] == "Cuckoo Agent!"
        assert self.get("/").json()["version"] == agent.AGENT_VERSION

    def test_status(self):
        r = self.get("/status")
        assert r.status_code == 200
        assert r.json()["message"] == "Analysis status"
        assert r.json()["status"] is None
        assert r.json()["description"] is None

        assert self.post("/status").status_code == 400
        assert self.get("/status").json()["status"] is None

        assert self.post("/status", data={"status": "foo"}).status_code == 200
        r = self.get("/status").json()
        assert r["status"] == "foo"
        assert r["description"] is None

        assert self.post("/status", data={
            "status": "foo",
            "description": "bar",
        }).status_code == 200
        r = self.get("/status").json()
        assert r["status"] == "foo"
        assert r["description"] == "bar"

    def test_system(self):
        assert self.get("/system").json()["system"] == platform.system()

    def test_environ(self):
        assert self.get("/environ").json()

    def test_mkdir(self):
        env = self.get("/environ").json()["environ"]
        assert self.post("/mkdir", data={
            "dirpath": os.path.join(env["PWD"], "mkdir.test"),
        }).status_code == 200

        r = self.post("/remove", data={
            "path": os.path.join(env["PWD"], "mkdir.test"),
        })
        assert r.status_code == 200
        assert r.json()["message"] == "Successfully deleted directory"

        assert self.post("/remove", data={
            "path": os.path.join(env["PWD"], "mkdir.test"),
        }).status_code == 404

        assert self.post("/mkdir", data={
            "dirpath": "/FOOBAR"
        }).status_code == 500

    def test_execute(self):
        assert self.post("/execute").status_code == 400

    def test_zipfile(self):
        assert self.post("/extract").status_code == 400

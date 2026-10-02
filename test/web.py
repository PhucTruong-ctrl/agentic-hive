#!/usr/bin/env python3
"""Focused dashboard control tests; no live sessions or Room are touched."""
import importlib.machinery
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
source = Path(__file__).resolve().parents[1] / "bin/hive-web"
loader = importlib.machinery.SourceFileLoader("hive_web_test", str(source))
spec = importlib.util.spec_from_loader(loader.name, loader)
web = importlib.util.module_from_spec(spec)
loader.exec_module(web)


class DashboardControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for member in ("alice", "bob", "beekeeper"):
            (self.root / "members" / member).mkdir(parents=True)
        self.root_patch = patch.object(web, "HIVE_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def request(self, path, payload, origin="http://hive.local"):
        handler = object.__new__(web.Handler)
        body = json.dumps(payload).encode()
        handler.path = path
        handler.headers = {"Content-Length": str(len(body)), "Origin": origin, "Host": "hive.local"}
        handler.rfile = io.BytesIO(body)
        responses = []
        handler._send = lambda status, data, _: responses.append((status, json.loads(data)))
        handler.do_POST()
        return responses[0]

    def test_room_all_posts_once_and_sends_to_every_agent(self):
        calls = []
        with patch.object(web, "run_hive", side_effect=lambda *args, **kwargs: calls.append((args, kwargs)) or "ok"):
            status, data = self.request("/api/room", {"message": "@all please check status"})
        self.assertEqual(status, 200)
        self.assertEqual(data["sent"], ["alice", "bob"])
        self.assertEqual(len([args for args, _ in calls if args[:2] == ("hive", "say")]), 1)
        sends = sorted(args[2] for args, _ in calls if args[:2] == ("hive-member", "send"))
        self.assertEqual(sends, ["alice", "bob"])

    def test_plain_room_post_uses_hive_cli(self):
        with patch.object(web, "run_hive", wraps=web.run_hive):
            web.run_hive("hive", "init")
            status, data = self.request("/api/room", {"message": "A note for the Room"})
        self.assertEqual(status, 200)
        self.assertEqual(data["sent"], [])
        room = (self.root / "ROOM.md").read_text()
        self.assertIn("member=beekeeper", room)
        self.assertIn("A note for the Room", room)

    def test_unknown_mention_never_posts(self):
        with patch.object(web, "run_hive") as run:
            status, data = self.request("/api/room", {"message": "@missing do work"})
        self.assertEqual(status, 400)
        self.assertIn("unknown member", data["error"])
        run.assert_not_called()

    def test_lifecycle_buttons_execute_session_commands(self):
        with patch.object(web, "run_hive", return_value="ok") as run:
            status, _ = self.request("/api/member", {"member": "alice", "action": "restart"})
        self.assertEqual(status, 200)
        run.assert_called_once_with("hive-member", "restart", "alice", "--force", "--no-attach")

    def test_cross_origin_command_is_rejected(self):
        with patch.object(web, "run_hive") as run:
            status, _ = self.request("/api/member", {"member": "alice", "action": "kill"}, "http://other.site")
        self.assertEqual(status, 403)
        run.assert_not_called()

    def test_member_card_uses_latest_room_message(self):
        posts = [{"member": "alice", "body": "first", "ts": "2026-10-01T10:00:00-04:00"},
                 {"member": "alice", "body": "latest", "ts": "2026-10-01T10:01:00-04:00"}]
        members = web.members(2, 0, posts)
        self.assertEqual(len(members), 2)
        self.assertEqual(next(m for m in members if m["member"] == "alice")["last_room"]["body"], "latest")

    def test_steer_uses_member_send(self):
        with patch.object(web, "run_hive", return_value="ok") as run:
            status, _ = self.request("/api/steer", {"member": "alice", "prompt": "do work"})
        self.assertEqual(status, 200)
        run.assert_called_once_with("hive-member", "send", "alice", "do work")

    def test_fragmented_websocket_input(self):
        class OneByteSocket:
            def __init__(self, data):
                self.data = bytearray(data)

            def recv(self, _):
                if not self.data:
                    return b""
                return bytes([self.data.pop(0)])

        payload = b"hello"
        mask = os.urandom(4)
        frame = bytes([0x81, 0x80 | len(payload)]) + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(payload))
        self.assertEqual(web.read_ws_frame(OneByteSocket(frame)), (1, payload))


if __name__ == "__main__":
    unittest.main()

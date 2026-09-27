from __future__ import annotations

import unittest
from unittest.mock import patch

from multi_agent_manager import identity


ROOT = "00000000-0000-4000-8000-000000000001"
CHILD = "00000000-0000-4000-8000-000000000002"
GRANDCHILD = "00000000-0000-4000-8000-000000000003"


class FakeStream:
    def __init__(self, threads):
        self.threads = threads
        self.calls = []

    def read(self, agent):
        self.calls.append(agent)
        return {"thread": self.threads[agent]}

    def close(self):
        pass


class IdentityTests(unittest.TestCase):
    def test_ancestry_uses_parent_thread_id_and_ignores_session_id(self):
        threads = {
            ROOT: {"id": ROOT, "parentThreadId": None, "sessionId": "unrelated-root-session"},
            CHILD: {"id": CHILD, "parentThreadId": ROOT, "sessionId": "unrelated-child-session",
                    "source": {"subAgent": {"thread_spawn": {"agent_path": "/root/worker"}}}},
            GRANDCHILD: {"id": GRANDCHILD, "parentThreadId": CHILD,
                         "source": {"subAgent": {"thread_spawn": {"agent_path": "/root/worker/helper"}}}},
        }
        stream = FakeStream(threads)
        with patch.object(identity.job_runtime.AppServerEventStream, "connect", return_value=stream):
            found = identity.read(GRANDCHILD)
        self.assertEqual((found.path, found.tree_root), ("/root/worker/helper", ROOT))
        self.assertEqual(stream.calls, [GRANDCHILD, CHILD, ROOT])

    def test_conflicting_native_path_is_rejected(self):
        threads = {
            ROOT: {"id": ROOT, "parentThreadId": None},
            CHILD: {"id": CHILD, "parentThreadId": ROOT,
                    "source": {"subAgent": {"thread_spawn": {"agent_path": "/root/other"}}}},
            GRANDCHILD: {"id": GRANDCHILD, "parentThreadId": CHILD,
                         "source": {"subAgent": {"thread_spawn": {"agent_path": "/root/worker/helper"}}}},
        }
        with patch.object(identity.job_runtime.AppServerEventStream, "connect", return_value=FakeStream(threads)):
            with self.assertRaisesRegex(identity.IdentityError, "conflicts"):
                identity.read(GRANDCHILD)

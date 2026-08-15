# Testing Steering

Core tests must run offline with fake providers and no API key. Test both success and fail-closed behavior: malformed input/output, low confidence, conflicts, missing IDs, provider failures, retries, chunking, ordering, and call count. Keep live-model tests optional and explicitly marked. After changes run targeted tests, then pytest, Ruff, mypy, offline evaluation, and CLI smoke test.

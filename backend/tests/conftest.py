import os
import tempfile
from pathlib import Path

# Point all session folders at a throwaway directory BEFORE the app's config is imported,
# so tests never touch real uploads or indexes.
_tmp = tempfile.mkdtemp(prefix="rag-tests-")
os.environ["DATA_DIR"] = os.path.join(_tmp, "data")
os.environ["STORAGE_DIR"] = os.path.join(_tmp, "storage")

# Stamp tests use their own copy of the synthetic reference stamps, so replacing
# backend/stamps/ with real stamps doesn't break them.
os.environ["STAMP_REFERENCES_DIR"] = str(Path(__file__).parent / "fixtures" / "stamps")

"""Generated protobuf and gRPC stubs for Chirp API.

This module adds the generated directory to sys.path so that
protoc's flat imports (e.g., `import common_pb2`) resolve correctly.
"""

import os
import sys

# protoc generates flat imports like "import common_pb2".
# When these files live inside a package, Python can't find them
# unless the generated directory is on sys.path.
_generated_dir = os.path.dirname(os.path.abspath(__file__))
if _generated_dir not in sys.path:
    sys.path.insert(0, _generated_dir)

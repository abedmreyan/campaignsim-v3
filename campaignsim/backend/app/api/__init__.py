"""API route module"""

from flask import Blueprint

graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
evaluation_bp = Blueprint('evaluation', __name__)
briefs_bp = Blueprint('briefs', __name__)

from . import graph        # noqa: E402, F401
from . import simulation   # noqa: E402, F401
from . import report       # noqa: E402, F401
from . import evaluation   # noqa: E402, F401
from . import auth         # noqa: E402, F401

# Re-export auth_bp (declared in auth.py) so app factory can import it from here
from .auth import auth_bp  # noqa: F401
from . import briefs  # noqa: E402, F401

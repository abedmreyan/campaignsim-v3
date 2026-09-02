"""API route module"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
graph_bp = Blueprint('graph', __name__)
simulation_bp = Blueprint('simulation', __name__)
report_bp = Blueprint('report', __name__)
evaluation_bp = Blueprint('evaluation', __name__)
briefs_bp = Blueprint('briefs', __name__)
channels_bp = Blueprint('channels', __name__)
designer_bp = Blueprint('designer', __name__)
insight_bp = Blueprint('insight', __name__)
data_bp = Blueprint('data', __name__)

from . import auth  # noqa: E402, F401
from . import graph  # noqa: E402, F401
from . import simulation_core  # noqa: E402, F401
from . import interviews  # noqa: E402, F401
from . import campaigns  # noqa: E402, F401
from . import segments  # noqa: E402, F401
from . import report  # noqa: E402, F401
from . import evaluation  # noqa: E402, F401
from . import briefs  # noqa: E402, F401
from . import channels  # noqa: E402, F401
from . import designer  # noqa: E402, F401
from . import insight  # noqa: E402, F401
from . import data  # noqa: E402, F401

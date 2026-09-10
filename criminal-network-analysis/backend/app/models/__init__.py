"""Import every model so Base.metadata sees all tables before create_all()."""
from app.models.user import User  # noqa: F401
from app.models.case import Case  # noqa: F401
from app.models.entities import Person, Organization, Vehicle, Phone, Location, Account  # noqa: F401
from app.models.relationship import Relationship  # noqa: F401
from app.models.event import Event  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.evidence import Evidence  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401

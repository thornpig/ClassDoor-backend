from flask import Blueprint

bp = Blueprint('api', __name__, url_prefix='/api/v1')

from .user import UserSchema, PersonSchema, DependentSchema
from .lesson import LessonSchema, RepeatedLessonSchema, TemplateLessonSchema
from .address import AddressSchema
from .class_session import ClassSchema, ClassSessionSchema
from .enrollment import EnrollmentSchema
from .notification import NotificationSchema, NotificationDeliverySchema
from .organization import OrganizationPersonSchema, OrganizationSchema
from .schedule import TimeSlotSchema, ScheduleSchema

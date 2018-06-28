import enum
from datetime import datetime, timedelta
from calendar import monthrange
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event
from .database import db, Model, SurrogatePK, TimestampMixin


class RepeatOptions(enum.Enum):
    NEVER = 1
    DAILY = 2
    WEEKLY = 3
    BIWEEKLY = 4
    MONTHLY = 5
    YEARLY = 6
    SPECIFIC = 7

    def get_repeat_datetime(self, dt=datetime.utcnow(), num=0):
        if self == self.NEVER:
            return None
        if num == 0:
            return dt
        elif self == self.DAILY:
            return dt + timedelta(days=num)
        elif self == self.WEEKLY:
            return dt + timedelta(weeks=num)
        elif self == self.BIWEEKLY:
            return dt + timedelta(weeks=2*num)
        elif self == self.MONTHLY:
            repeat_year = dt.year + (dt.month + num - 1) // 12
            repeat_month = (dt.month + num - 1) % 12 + 1
            repeat_month_length = monthrange(repeat_year, repeat_month)[1]
            repeat_day = (repeat_month_length if dt.day > repeat_month_length
                          else dt.day)
            return dt.replace(year=repeat_year, month=repeat_month,
                              day=repeat_day)
        elif self == self.YEARLY:
            repeat_year = dt.year + num
            repeat_dt_month_length = monthrange(repeat_year, dt.month)[1]
            repeat_day = (repeat_dt_month_length if dt.day >
                          repeat_dt_month_length else dt.day)
            return dt.replace(year=repeat_year, day=repeat_day)
        elif self == self.SPECIFIC:
            return None

    def delta_in_days(self, dt=None, num=0):
        if self == self.NEVER or num == 0:
            return 0
        elif self == self.DAILY:
            return num
        elif self == self.WEEKLY:
            return 7 * num
        elif self == self.BIWEEKLY:
            return 14 * num
        elif self in [self.MONTHLY, self.YEARLY]:
            assert dt is not None, 'needs dt to determine the delta'
            return (self.get_repeat_datetime(dt, num) - dt).days
        elif self == self.SPECIFIC:
            return None


class TimeSlot(SurrogatePK, Model):
    __tablename__ = 'time_slot'
    start_at = db.Column(db.DateTime, nullable=False)
    # duration is in minutes
    duration = db.Column(db.Integer, default=0, nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'))

    def __repr__(self):
        return '<TimeSlot> {} seconds long that starts at: {}'.format(
            self.duration, self.start_at)


class RepeatTimeSlot(SurrogatePK, Model):
    __tablename__ = 'repeat_time_slot'
    base_time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'))
    repeat_option = db.Column(
        db.Enum(RepeatOptions, validate_strings=True),
        default=RepeatOptions.NEVER,
        nullable=False
    )
    repeat_num = db.Column(db.Integer, default=0, nullable=False)
    # for repeat_option == SPECIFIC only
    repeat_at = db.Column(db.DateTime)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'))
    start_at = db.Column(db.DateTime)

    base_time_slot = db.relationship(
        'TimeSlot',
        lazy='subquery'
    )

    def get_start_at(self):
        if self.repeat_option == RepeatOptions.SPECIFIC:
            assert self.repeat_at is not None, (
                'repeat_at needs to be set'
                'for repeat_option == SPECIFIC'
            )
            return self.repeat_at
        else:
            return self.repeat_option.get_repeat_datetime(
                self.base_time_slot.start_at, self.repeat_num)


@event.listens_for(RepeatTimeSlot, 'before_insert')
@event.listens_for(RepeatTimeSlot, 'before_update')
def auto_set_start_at_for_repeat_time_slot(mapper, connection, target):
    target.start_at = target.get_start_at()


class Schedule(SurrogatePK, Model):
    __tablename__ = 'schedule'
    repeat_option = db.Column(
        db.Enum(RepeatOptions, validate_strings=True),
        default=RepeatOptions.NEVER,
        nullable=False
    )
    repeat_end_at = db.Column(db.DateTime)
    base_time_slots = db.relationship(
        'TimeSlot',
        lazy='subquery',
        order_by=(TimeSlot.start_at)
    )
    # repeat_time_slots include those for base_time_slots
    repeat_time_slots = db.relationship(
        'RepeatTimeSlot',
        lazy='subquery',
        order_by=(RepeatTimeSlot.start_at,)
    )

    @property
    def num_of_time_slots(self):
        return len(self.repeat_time_slots)

    def get_repeat_time_slots(self):
        if self.repeat_option == RepeatOptions.SPECIFIC:
            return self.repeat_time_slots
        elif self.repeat_option == RepeatOptions.NEVER:
            return [RepeatTimeSlot(base_time_slot=ts,
                                   repeat_num=0,
                                   repeat_option=self.repeat_option)
                    for ts in self.base_time_slots]
        elif self.repeat_end_at is None:
            return None

        repeat_num = 0
        all_rep_slots = []
        base_slots = self.base_time_slots
        while len(base_slots) > 0:
            new_base_slots = []
            for base_time_slot in base_slots:
                new_start_at = (
                    self.repeat_option.get_repeat_datetime(
                        base_time_slot.start_at,
                        repeat_num
                    )
                )
                print(new_start_at)
                if new_start_at > self.repeat_end_at:
                    break
                new_rep_slot = RepeatTimeSlot(base_time_slot=base_time_slot,
                                              repeat_num=repeat_num,
                                              repeat_option=self.repeat_option)
                all_rep_slots.append(new_rep_slot)
                new_base_slots.append(base_time_slot)
            repeat_num = repeat_num + 1
            base_slots = new_base_slots

        return all_rep_slots


# @event.listens_for(Schedule, 'before_insert')
# @event.listens_for(Schedule, 'before_update')
# def auto_set_repeat_time_slots_for_schedule(mapper, connection, target):
#     target.repeat_time_slots = target.get_repeat_time_slots()

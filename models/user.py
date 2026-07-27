from tortoise import fields
from tortoise.models import Model


class User(Model):
    """
    Kept for whatever else identifies people by bale_id elsewhere in the
    system (e.g. the Bale bot). Not used by the participant-upload API at
    all -- that endpoint takes no caller identity.
    """

    id = fields.IntField(pk=True)
    bale_id = fields.BigIntField(unique=True)
    is_super_user = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "users"

    def __str__(self):
        return str(self.bale_id)

    @classmethod
    async def get_by_bale_id(cls, bale_id: int) -> "User | None":
        return await cls.get_or_none(bale_id=bale_id)


class Event(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255, unique=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "events"

    def __str__(self):
        return self.name


class Participant(Model):
    id = fields.IntField(pk=True)
    full_name = fields.CharField(max_length=255, null=True)
    national_id = fields.CharField(max_length=10, null=True)
    province = fields.CharField(max_length=100, null=True)
    university = fields.CharField(max_length=255, null=True)
    position = fields.CharField(max_length=100, null=True)
    phone_number = fields.CharField(max_length=20, unique=True, index=True)
    email = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


    user = fields.OneToOneField(
        "models.User",
        related_name="participant",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "participants"



        

class EventParticipant(Model):
    """
    Junction table: one row per (event, participant) pair, holding only
    facts true of that pairing -- the PDF license generated for this
    participant at this event.
    """

    id = fields.IntField(pk=True)
    event = fields.ForeignKeyField(
        "models.Event", related_name="event_participants", source_field="event_id"
    )
    participant = fields.ForeignKeyField(
        "models.Participant",
        related_name="event_participants",
        source_field="participant_id",
    )

    license_file = fields.CharField(max_length=500, null=True)
    original_filename = fields.CharField(max_length=255, null=True)

    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "event_participants"
        unique_together = (("event", "participant"),)
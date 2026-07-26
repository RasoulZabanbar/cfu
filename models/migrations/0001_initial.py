from tortoise import migrations
from tortoise.migrations import operations as ops
from tortoise.fields.base import OnDelete
from tortoise import fields

class Migration(migrations.Migration):
    initial = True

    operations = [
        ops.CreateModel(
            name='Event',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('name', fields.CharField(unique=True, max_length=255)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'events', 'app': 'models', 'pk_attr': 'id'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='User',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('bale_id', fields.BigIntField(unique=True)),
                ('is_super_user', fields.BooleanField(default=False)),
                ('is_active', fields.BooleanField(default=True)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
            ],
            options={'table': 'users', 'app': 'models', 'pk_attr': 'id', 'table_description': 'Kept for whatever else identifies people by bale_id elsewhere in the'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='Participant',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('full_name', fields.CharField(null=True, max_length=255)),
                ('national_id', fields.CharField(null=True, max_length=10)),
                ('province', fields.CharField(null=True, max_length=100)),
                ('university', fields.CharField(null=True, max_length=255)),
                ('position', fields.CharField(null=True, max_length=100)),
                ('phone_number', fields.CharField(unique=True, db_index=True, max_length=20)),
                ('email', fields.CharField(null=True, max_length=255)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
                ('events', fields.ManyToManyField('models.Event', unique=True, db_constraint=True, through='event_participants', forward_key='event_id', backward_key='participant_id', related_name='participants', on_delete=OnDelete.CASCADE)),
                ('user', fields.OneToOneField('models.User', source_field='user_id', null=True, db_constraint=True, to_field='id', related_name='participant', on_delete=OnDelete.SET_NULL)),
            ],
            options={'table': 'participants', 'app': 'models', 'pk_attr': 'id', 'table_description': 'One row per phone_number (unique, the natural key). Every column'},
            bases=['Model'],
        ),
        ops.CreateModel(
            name='EventParticipant',
            fields=[
                ('id', fields.IntField(generated=True, primary_key=True, unique=True, db_index=True)),
                ('event', fields.ForeignKeyField('models.Event', source_field='event_id', db_constraint=True, to_field='id', related_name='event_participants', on_delete=OnDelete.CASCADE)),
                ('participant', fields.ForeignKeyField('models.Participant', source_field='participant_id', db_constraint=True, to_field='id', related_name='event_participants', on_delete=OnDelete.CASCADE)),
                ('license_file', fields.CharField(null=True, max_length=500)),
                ('original_filename', fields.CharField(null=True, max_length=255)),
                ('created_at', fields.DatetimeField(auto_now=False, auto_now_add=True)),
                ('updated_at', fields.DatetimeField(auto_now=True, auto_now_add=False)),
            ],
            options={'table': 'event_participants', 'app': 'models', 'unique_together': (('event', 'participant'),), 'pk_attr': 'id', 'table_description': 'Junction table: one row per (event, participant) pair, holding only'},
            bases=['Model'],
        ),
    ]

from pydantic import BaseModel, ConfigDict


class EventOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class ParticipantOut(BaseModel):
    id: int
    full_name: str | None
    national_id: str | None
    province: str | None
    university: str | None
    position: str | None
    phone_number: str
    email: str | None

    model_config = ConfigDict(from_attributes=True)


class ParticipantUploadResponse(BaseModel):
    event: EventOut
    participant: ParticipantOut
    participant_created: bool
    event_participant_created: bool
    license_file: str
import os
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status


from boot.config import get_env_setup
from models.user import Event, EventParticipant, Participant
from services.schemas import ParticipantUploadResponse
from services.phone import normalize_phone


_env_config = get_env_setup()
router = APIRouter(prefix="/participants", tags=["participants"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}


_OPTIONAL_FIELDS = ("full_name", "national_id", "province", "university", "position", "email")


@router.post("/upload", response_model=ParticipantUploadResponse)
async def upload_participant(
    event_name: str = Form(...),
    phone_number: str = Form(...),
    full_name: str | None = Form(None),
    national_id: str | None = Form(None),
    province: str | None = Form(None),
    university: str | None = Form(None),
    position: str | None = Form(None),
    email: str | None = Form(None),
    file: UploadFile = File(...),
):
    """
    One call = one Excel row + its generated PDF.
    ...
    """
    event_name = event_name.strip()
    phone_number = normalize_phone(phone_number)

    if not event_name:
        raise HTTPException(status_code=400, detail="event_name is required")
    if not phone_number:
        raise HTTPException(status_code=400, detail="phone_number is required")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    event, _ = await Event.get_or_create(name=event_name)

    incoming = {
        "full_name": full_name,
        "national_id": national_id,
        "province": province,
        "university": university,
        "position": position,
        "email": email,
    }

    participant = await Participant.get_or_none(phone_number=phone_number)
    participant_created = False
    if participant is None:
        participant = await Participant.create(phone_number=phone_number, **incoming)
        participant_created = True
    else:
        changed = {k: v for k, v in incoming.items() if v is not None and v != getattr(participant, k)}
        if changed:
            for key, value in changed.items():
                setattr(participant, key, value)
            await participant.save(update_fields=[*changed.keys(), "updated_at"])

    # Store the PDF on disk under a per-event folder; filename is
    # unique regardless of what the client named it.
    event_dir = os.path.join(_env_config.storage_dir, str(event.id))
    os.makedirs(event_dir, exist_ok=True)
    stored_path = os.path.join(event_dir, f"{participant.id}_{uuid.uuid4().hex[:8]}.pdf")

    contents = await file.read()
    with open(stored_path, "wb") as f:
        f.write(contents)

    event_participant = await EventParticipant.get_or_none(event=event, participant=participant)
    event_participant_created = False
    if event_participant is None:
        event_participant = await EventParticipant.create(
            event=event,
            participant=participant,
            license_file=stored_path,
            original_filename=file.filename,
        )
        event_participant_created = True
    else:
        old_path = event_participant.license_file
        event_participant.license_file = stored_path
        event_participant.original_filename = file.filename
        await event_participant.save(update_fields=["license_file", "original_filename", "updated_at"])
        if old_path and old_path != stored_path and os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass  # stale file left behind is not worth failing the request over

    return ParticipantUploadResponse(
        event=event,
        participant=participant,
        participant_created=participant_created,
        event_participant_created=event_participant_created,
        license_file=stored_path,
    )
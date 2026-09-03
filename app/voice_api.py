from __future__ import annotations

from io import BytesIO
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from voice_recovery import (
    start_voice_recovery,
    process_conversation_turn,
    transcribe_hinglish_audio,
    verify_payment,
)


router = APIRouter(
    prefix="/voice",
    tags=["Hinglish Voice Recovery"],
)


# =================================================================
# REQUEST MODELS
# =================================================================

class VoiceStartRequest(BaseModel):
    payment_id: str
    amount: float = Field(gt=0)
    failure_reason: str


class VoiceTurnRequest(BaseModel):
    session: dict[str, Any]
    message: str = Field(min_length=1)


class VoiceVerifyRequest(BaseModel):
    promise_id: str
    payment_amount: float = Field(gt=0)


# =================================================================
# START VOICE SESSION
# =================================================================

@router.post("/start")
def voice_start(
    request: VoiceStartRequest,
) -> dict[str, Any]:

    try:
        session = start_voice_recovery(
            payment_id=request.payment_id,
            amount=request.amount,
            failure_reason=request.failure_reason,
        )

        return {
            "success": True,
            "session": session,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# PROCESS HINGLISH CONVERSATION TURN
# =================================================================

@router.post("/turn")
def voice_turn(
    request: VoiceTurnRequest,
) -> dict[str, Any]:

    try:
        result = process_conversation_turn(
            request.session,
            request.message,
        )

        return {
            "success": True,
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# SPEECH TO TEXT
# =================================================================

@router.post("/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
) -> dict[str, Any]:

    try:
        audio_bytes = await audio.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="Audio recording is empty.",
            )

        audio_buffer = BytesIO(audio_bytes)

        result = transcribe_hinglish_audio(
            audio_buffer
        )

        return {
            "success": True,
            "result": result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# =================================================================
# PAYMENT VERIFICATION
# =================================================================

@router.post("/verify")
def voice_verify(
    request: VoiceVerifyRequest,
) -> dict[str, Any]:

    try:
        result = verify_payment(
            request.promise_id,
            request.payment_amount,
        )

        return {
            "success": True,
            "result": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
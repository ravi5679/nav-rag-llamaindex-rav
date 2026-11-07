"""Account endpoints: /api/v1/auth/signup, /login, /me, /logout."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool

from common import auth, index_store
from common.schemas import AuthResponse, AuthUser, Credentials
from common.security import verify_api_key

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(verify_api_key)])


def _auth_response(email: str, token: str, session_id: str) -> AuthResponse:
    return AuthResponse(token=token, session_id=session_id, user=AuthUser(email=email))


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(body: Credentials):
    try:
        # scrypt hashing is deliberately slow: keep it off the event loop
        return _auth_response(*await run_in_threadpool(auth.signup, body.email, body.password))
    except auth.AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def login(body: Credentials):
    try:
        return _auth_response(*await run_in_threadpool(auth.login, body.email, body.password))
    except auth.AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me", response_model=AuthUser)
async def me(token: str = Depends(auth.get_token)):
    try:
        email, _session_id = auth.authenticate(token)
    except auth.AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return AuthUser(email=email)


@router.post("/logout", status_code=204)
async def logout(token: str = Depends(auth.get_token)):
    # The user's work is finished: delete their files, embeddings and indexes (all RAG types) right away
    session_id = auth.logout(token)
    if session_id:
        await run_in_threadpool(index_store.delete_session, session_id)

"""Main module."""

import base64
import os
import tarfile
import uuid

from fastapi import Body, FastAPI, File, HTTPException, Security, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from telos.language import build_model
from telos.transformations import m2t_python

HAS_DOCKER_EXEC = os.getenv("HAS_DOCKER_EXEC", False)
API_KEY = os.getenv("API_KEY", "API_KEY")
TMP_DIR = "/tmp/telos"


if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)


api_keys = [API_KEY]

api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header in api_keys:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key",
    )


api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidationModel(BaseModel):
    name: str
    model: str


class TransformationModel(BaseModel):
    name: str
    model: str


@api.post("/validate")
async def validate(model: ValidationModel, api_key: str = Security(get_api_key)):
    text = model.model
    if len(text) == 0:
        return 404
    resp = {"status": 200, "message": ""}
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, f"model_for_validation-{u_id}.telos")
    with open(fpath, "w") as f:
        f.write(text)
    try:
        model = build_model(fpath)
        print("Model validation success!!")
        resp["message"] = "Model validation success"
    except Exception as e:
        print("Exception while validating model. Validation failed!!")
        print(e)
        resp["status"] = 404
        resp["message"] = str(e)
        raise HTTPException(status_code=400, detail=f"Validation error: {e}")
    return resp


@api.post("/validate/file")
async def validate_file(file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    print(f"Validation for request: file=<{file.filename}>," + f" descriptor=<{file.file}>")
    resp = {"status": 200, "message": ""}
    fd = file.file
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, f"model_for_validation-{u_id}.telos")
    with open(fpath, "w") as f:
        f.write(fd.read().decode("utf8"))
    try:
        build_model(fpath)
    except Exception as e:
        resp["status"] = 404
        resp["message"] = str(e)
    return resp


@api.get("/validate/base64")
async def validate_b64(fenc: str = "", api_key: str = Security(get_api_key)):
    if len(fenc) == 0:
        return 404
    resp = {"status": 200, "message": ""}
    fdec = base64.b64decode(fenc)
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, "model_for_validation-{}.telos".format(u_id))
    with open(fpath, "wb") as f:
        f.write(fdec)
    try:
        build_model(fpath)
    except Exception as e:
        resp["status"] = 404
        resp["message"] = str(e)
    return resp


@api.post("/generate")
async def gen_from_model(
    gen_auto_model: TransformationModel = Body(...),
    api_key: str = Security(get_api_key),
):
    model = gen_auto_model.model
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.telos")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")
    if not os.path.exists(gen_path):
        os.mkdir(gen_path)
    with open(model_path, "w") as f:
        f.write(model)
    tarball_path = os.path.join(TMP_DIR, f"{u_id}.tar.gz")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")
    try:
        out_dir = m2t_python(model_path, gen_path)
        make_tarball(tarball_path, out_dir)
        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Codintxt.Transformation error: {e}")


@api.post("/generate/file")
async def gen_from_file(model_file: UploadFile = File(...), api_key: str = Security(get_api_key)):
    print(
        f"Generate for request: file=<{model_file.filename}>," + f" descriptor=<{model_file.file}>"
    )
    resp = {"status": 200, "message": ""}
    fd = model_file.file
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.telos")
    tarball_path = os.path.join(TMP_DIR, f"{u_id}.tar.gz")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")
    with open(model_path, "w") as f:
        f.write(fd.read().decode("utf8"))
    try:
        out_dir = m2t_python(model_path, gen_path)
        make_tarball(tarball_path, out_dir)
        return FileResponse(
            tarball_path,
            filename=os.path.basename(tarball_path),
            media_type="application/x-tar",
        )
    except Exception as e:
        print(e)
        resp["status"] = 404
        return resp


def make_tarball(fout, source_dir):
    with tarfile.open(fout, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

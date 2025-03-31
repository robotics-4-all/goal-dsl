"""Main module."""

import uuid
import os
import base64
from typing import Optional
import subprocess

import tarfile

from goal_dsl.language import build_model
from goal_dsl.generator import m2t_python

from fastapi import FastAPI, File, UploadFile, status, HTTPException, Security, Body
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

HAS_DOCKER_EXEC = os.getenv("HAS_DOCKER_EXEC", False)
API_KEY = os.getenv("API_KEY", "API_KEY")
TMP_DIR = '/tmp/goaldsl'


if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)


api_keys = [
    API_KEY
]

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
    name = model.name
    if len(text) == 0:
        return 404
    resp = {"status": 200, "message": ""}
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(TMP_DIR, f"model_for_validation-{u_id}.goal")
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
async def validate_file(file: UploadFile = File(...),
                        api_key: str = Security(get_api_key)):
    print(f'Validation for request: file=<{file.filename}>,' + \
          f' descriptor=<{file.file}>')
    resp = {
        'status': 200,
        'message': ''
    }
    fd = file.file
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(
        TMP_DIR,
        f'model_for_validation-{u_id}.goal'
    )
    with open(fpath, 'w') as f:
        f.write(fd.read().decode('utf8'))
    try:
        model, _ = build_model(fpath)
    except Exception as e:
        resp['status'] = 404
        resp['message'] = e
    return resp


@api.get("/validate/base64")
async def validate_b64(fenc: str = '',
                       api_key: str = Security(get_api_key)):
    if len(fenc) == 0:
        return 404
    resp = {
        'status': 200,
        'message': ''
    }
    fdec = base64.b64decode(fenc)
    u_id = uuid.uuid4().hex[0:8]
    fpath = os.path.join(
        TMP_DIR,
        'model_for_validation-{}.goal'.format(u_id)
    )
    with open(fpath, 'wb') as f:
        f.write(fdec)
    try:
        model, _ = build_model(fpath)
    except Exception as e:
        resp['status'] = 404
        resp['message'] = e
    return resp


@api.post("/generate")
async def gen_from_model(
    gen_auto_model: TransformationModel = Body(...),
    api_key: str = Security(get_api_key),
):
    resp = {"status": 200, "message": "", "model_json": ""}
    model = gen_auto_model.model
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(TMP_DIR, f"model-{u_id}.auto")
    gen_path = os.path.join(TMP_DIR, f"gen-{u_id}")
    if not os.path.exists(gen_path):
        os.mkdir(gen_path)
    with open(model_path, "w") as f:
        f.write(model)
    tarball_path = os.path.join(
        TMP_DIR,
        f'{u_id}.tar.gz'
    )
    gen_path = os.path.join(
        TMP_DIR,
        f'gen-{u_id}'
    )
    try:
        out_dir = m2t_python(model_path, gen_path)
        make_tarball(tarball_path, out_dir)
        return FileResponse(tarball_path,
                            filename=os.path.basename(tarball_path),
                            media_type='application/x-tar')
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Codintxt.Transformation error: {e}"
        )


@api.post("/generate/file")
async def gen_from_file(model_file: UploadFile = File(...),
                        api_key: str = Security(get_api_key)):
    print(f'Generate for request: file=<{model_file.filename}>,' + \
          f' descriptor=<{model_file.file}>')
    resp = {
        'status': 200,
        'message': ''
    }
    fd = model_file.file
    u_id = uuid.uuid4().hex[0:8]
    model_path = os.path.join(
        TMP_DIR,
        f'model-{u_id}.goal'
    )
    tarball_path = os.path.join(
        TMP_DIR,
        f'{u_id}.tar.gz'
    )
    gen_path = os.path.join(
        TMP_DIR,
        f'gen-{u_id}'
    )
    with open(model_path, 'w') as f:
        f.write(fd.read().decode('utf8'))
    try:
        out_dir = m2t_python(model_path, gen_path)
        make_tarball(tarball_path, out_dir)
        print(f'Sending tarball {tarball_path}')
        return FileResponse(tarball_path,
                            filename=os.path.basename(tarball_path),
                            media_type='application/x-tar')
    except Exception as e:
        print(e)
        resp['status'] = 404
        return resp


if HAS_DOCKER_EXEC:
    @api.post("/execute")
    async def execute(model_file: UploadFile = File(...),
                      container: str = 'subprocess',
                      wait: bool = False,
                      api_key: str = Security(get_api_key)):
        print(f'Run/Execute for request: file=<{model_file.filename}>,' + \
              f' descriptor=<{model_file.file}>')
        resp = {
            'status': 200,
            'message': ''
        }
        fd = model_file.file
        u_id = uuid.uuid4().hex[0:8]
        model_path = os.path.join(
            TMP_DIR,
            f'model-{u_id}.goal'
        )
        gen_path = os.path.join(
            TMP_DIR,
            f'gen-{u_id}'
        )
        with open(model_path, 'w') as f:
            f.write(fd.read().decode('utf8'))
        try:
            out_dir = m2t_python(model_path, gen_path)
            if container == 'docker':
                img = build_docker_image(out_dir)
                print('Executing within Container...')
                container = run_container(img.id, u_id)
                print('Goal-Checker Container created - [{}:{}]'.format(
                    container.name, container.id))
            elif container == 'subprocess':
                exec_path = os.path.join(out_dir, 'goal_checker.py')
                pid = run_subprocess(exec_path)
                if wait:
                    pid.wait()

        except Exception as e:
            print(e)
            resp['status'] = 404
        return resp


def run_subprocess(exec_path):
    pid = subprocess.Popen(['python3', exec_path], close_fds=True)
    return pid


if HAS_DOCKER_EXEC:
    def run_container(img_id, u_id):
        container = docker_client.containers.run(
            img_id,
            name=f'goalT-{u_id}',
            detach=True,
            network_mode='host',
        )
        return container


if HAS_DOCKER_EXEC:
    def build_docker_image(dpath: str):
        img, logs = docker_client.images.build(path=dpath)
        print(logs)
        return img


def make_tarball(fout, source_dir):
    with tarfile.open(fout, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))

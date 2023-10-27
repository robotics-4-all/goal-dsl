"""Main module."""

import uuid
import os
import base64
from typing import Optional
import subprocess

import tarfile

from goal_dsl.language import build_model
from goal_dsl.codegen import generate as generate_model

from fastapi import FastAPI, File, UploadFile, status
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

HAS_DOCKER_EXEC = os.getenv("HAS_DOCKER_EXEC", False)

if HAS_DOCKER_EXEC:
    import docker
    docker_client = docker.from_env()

api = FastAPI()
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


TMP_DIR = '/tmp/goaldsl'


if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)


@api.get("/", response_class=HTMLResponse)
async def root():
    return """
<html>
<head>
<style>
html,body{
    margin:0;
    height:100%;
}
img{
  display:block;
  width:100%; height:100%;
  object-fit: cover;
}
</style>
</head>
<body>
 <img src="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fnews.images.itv.com%2Fimage%2Ffile%2F492835%2Fimg.jpg&f=1&nofb=1" alt="">
</body>
</html>
    """


@api.post("/validate/file")
async def validate_file(file: UploadFile = File(...)):
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
async def validate_b64(fenc: str = ''):
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
async def generate(model_file: UploadFile = File(...)):
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
        out_dir = generate_model(model_path, gen_path)
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
                      wait: bool = False):
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
            out_dir = generate_model(model_path, gen_path)
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


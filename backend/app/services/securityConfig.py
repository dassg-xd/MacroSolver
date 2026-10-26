from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.services.configuracion import configuraciones

def configurar_cors(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuraciones.cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

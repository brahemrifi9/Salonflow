from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, database

# Esta línea crea la tabla físicamente en PostgreSQL si no existe
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="SalonFlow MVP")

@app.get("/")
def read_root():
    return {"status": "online", "database": "connected"}

@app.get("/check-db")
def check_db(db: Session = Depends(database.get_db)):
    # Si esto funciona, es que Python puede leer la DB
    return {"message": "Conexión con la base de datos exitosa!"}

from pydantic import BaseModel

# Esto define qué datos esperamos recibir del usuario
class ClienteCreate(BaseModel):
    nombre: str
    email: str

@app.post("/clientes/")
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(database.get_db)):
    # Creamos el objeto del modelo con los datos recibidos
    nuevo_cliente = models.Cliente(nombre=cliente.nombre, email=cliente.email)
    
    # Lo añadimos a la sesión y guardamos en la DB
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    
    return {"message": "Cliente creado!", "data": nuevo_cliente}

@app.get("/clientes/")
def listar_clientes(db: Session = Depends(database.get_db)):
    return db.query(models.Cliente).all()
from fastapi import FastAPI
from .database import engine, Base
from .routers import auth, investments, admin, user_analytics, users, divestments, company_analytics
from fastapi.middleware.cors import CORSMiddleware
from .config import settings_api

app = FastAPI()
Base.metadata.create_all(bind=engine)
# About CORS
# list of URLs api can talk. if all origins = ["*"]
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(investments.router)
app.include_router(admin.router)
app.include_router(users.router)
app.include_router(divestments.router)
app.include_router(user_analytics.router)
app.include_router(company_analytics.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host=f"{settings_api.app_host}",port=settings_api.app_port)
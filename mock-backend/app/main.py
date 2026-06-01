from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_tables
from app.routers import analytics, employees, products, shoppers, transactions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(title="Lumen & Stone Data API", docs_url="/docs", lifespan=lifespan)

app.include_router(employees.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")
app.include_router(shoppers.router, prefix="/api/v1")
app.include_router(transactions.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Lumen & Stone Data API")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    args = parser.parse_args()

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=True)

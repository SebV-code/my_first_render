import csv
import os
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field

DESCRIPTION = """
Welcome to the Jedha Render demo API. This app shows a small FastAPI service you can deploy with Docker.

## Introduction
* `/` returns a welcome message
* `/health` returns service status
* `/greetings` returns a hello message

## Blog
* `/blog-articles/{blog_id}` reads a local CSV of sample articles
* `/create-blog-article` appends an article to the local CSV
* `/post-picture` accepts an uploaded file name

## Prediction
* `/predict` estimates salary from years of experience with a tiny fixed formula
"""

app = FastAPI(
    title="Jedha Render Demo API",
    description=DESCRIPTION,
    version="0.2",
    contact={"name": "Jedha", "url": "https://jedha.co"},
)

ARTICLES_PATH = Path(__file__).parent / "data" / "articles.csv"


class BlogArticle(BaseModel):
    title: str
    content: str
    author: str = "Anonymous Author"


class PredictionFeatures(BaseModel):
    YearsExperience: float = Field(ge=0, le=50)


def _load_articles() -> list[dict]:
    with ARTICLES_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_articles(rows: list[dict]) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with ARTICLES_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@app.get("/")
async def index():
    return {
        "message": "Hello from the Render demo API. Open /docs to try the endpoints."
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/greetings")
async def greetings(name: str = "there"):
    return {"message": f"Hello {name}. How are you today?"}


@app.get("/blog-articles/{blog_id}")
async def read_blog_article(blog_id: int):
    articles = _load_articles()
    if blog_id < 0 or blog_id >= len(articles):
        return {"msg": "We don't have that many articles!"}
    article = articles[blog_id]
    return {
        "title": article.get("title"),
        "content": article.get("content"),
        "author": article.get("author"),
    }


@app.post("/create-blog-article")
async def create_blog_article(blog_article: BlogArticle):
    rows = _load_articles()
    next_id = 1
    if rows:
        try:
            next_id = max(int(row.get("id", 0)) for row in rows) + 1
        except ValueError:
            next_id = len(rows) + 1
    new_row = {
        "id": str(next_id),
        "title": blog_article.title,
        "content": blog_article.content,
        "author": blog_article.author,
    }
    rows.append(new_row)
    _write_articles(rows)
    return {"created": new_row, "total_articles": len(rows)}


@app.post("/post-picture")
async def post_picture(file: UploadFile = File(...)):
    return {"picture": file.filename}


@app.post("/predict")
async def predict(features: PredictionFeatures):
    prediction = 25792.2 + 9449.96 * features.YearsExperience
    return {"prediction": round(prediction, 2)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port)

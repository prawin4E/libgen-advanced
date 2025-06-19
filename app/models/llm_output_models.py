from pydantic import BaseModel, Field
from typing import List

class BookDetails(BaseModel):
    title: str = Field(..., description="The title of the book")
    author: str = Field("", description="Author of the book")
    year: int = Field(0, description="Year of publication")
    pages: int = Field(0, description="Number of pages in the book")
    size: float = Field(0.0, description="Size of the book file in MB")
    file_url: str = Field(..., description="URL to download the book file")
    direct_download_url: str = Field(..., description="Direct download URL for the book file")
    extension: str = Field(..., description="File extension of the book file")
    md5: str = Field(..., description="The MD5 hash of the book file")

class BookSortOutput(BaseModel):
    books: List[BookDetails] = Field(...,description="List of books to sort in the best reading order.")
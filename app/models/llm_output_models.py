from pydantic import BaseModel, Field
from typing import List, Optional

class BookDetails(BaseModel):
    title: Optional[str] = Field(None, description="The title of the book")
    author: Optional[str] = Field(None, description="Author of the book")
    year: Optional[int] = Field(None, description="Year of publication")
    pages: Optional[int] = Field(None, description="Number of pages in the book")
    size: Optional[float] = Field(None, description="Size of the book file in MB")
    file_url: Optional[str] = Field(None, description="URL to download the book file")
    direct_download_url: Optional[str] = Field(None, description="Direct download URL for the book file")
    extension: Optional[str] = Field(None, description="File extension of the book file")
    md5: Optional[str] = Field(None, description="The MD5 hash of the book file")

class BookSortOutput(BaseModel):
    books: List[BookDetails] = Field(...,description="List of books to sort in the best reading order.")
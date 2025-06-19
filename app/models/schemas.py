from pydantic import BaseModel, Field
from typing import Optional

class BookDetails(BaseModel):
    title: str = Field("", description="The title of the book")
    author: Optional[str] = Field("", description="Author of the book")
    year: Optional[int] =  Field(0, description="Year of publication")
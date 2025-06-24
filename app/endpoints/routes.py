import os
import tempfile
from app.endpoints.route_validator import RouteValidator
from fastapi import APIRouter, UploadFile, Depends, File
from app.models.schemas import BookDetails
from app.core.libgen_advanced import LibGenScraper
from fastapi.responses import FileResponse
from app.core.llm_book_sorter import LLMBookSorter
from app.endpoints.errors import APIException
from app.utils.libgen_downloader import downloader

router = APIRouter()

scraper = LibGenScraper()

@router.post("/get_book")
async def get_book(book_details: BookDetails = Depends(RouteValidator.validate_get_book)):
    """
    Endpoint to get book details.
    """
    parts = [book_details.title]

    if book_details.author:
        parts.append(book_details.author)
    if book_details.year:
        parts.append(str(book_details.year))

    book_name = ", ".join(parts)
    results = scraper.search(book_name, results_per_page=100)
    if not results:
        raise APIException(404)
    csv_path = os.path.join(tempfile.gettempdir(), book_name + ".csv")
    scraper.save_to_csv(results, csv_path)
    sorted_books = LLMBookSorter(csv_path, book_name).sort()
    for book in sorted_books.books:
        link, cover_image_url = downloader.get_direct_download_url(md5=book.md5)
        if link is not None:
            data = book.model_dump()
            data["link"] = link
            data["cover_image_url"] = cover_image_url
            return data
    raise APIException(404)

@router.post("/download_book")
async def download_book(md5: str):
    """
    Endpoint to download a book from LibGen.
    """
    if not md5:
        raise APIException(400)

    try:
        link = downloader.get_direct_download_url(md5=md5)
        return {"link": link}
    except Exception as e:
        raise APIException(500)

# @router.post("/upload_csv")
# async def upload_csv(file: UploadFile = File(...)):

    

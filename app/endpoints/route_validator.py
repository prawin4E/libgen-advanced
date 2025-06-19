from dataclasses import dataclass
from fastapi import UploadFile, File
from typing import Set, Optional
from app.endpoints.errors import APIException
from app.models.schemas import BookDetails


class RouteValidator:
    allowed_extensions: Set[str] = {"csv"}

    @staticmethod
    def validate_csv_uploader(csv_file: UploadFile = File(...)) -> UploadFile:
        """
        Validates that the uploaded file is a CSV.
        """
        try:
            ext = RouteValidator._extract_extension(csv_file)
            RouteValidator._validate_file_type(ext)
            return csv_file
        except AttributeError:
            raise APIException(500, detail="Invalid file upload")

    @staticmethod
    def validate_get_book(book_details: BookDetails) -> BookDetails:
        """
        Validates the book details provided in the request.
        """
        if book_details.title is None or book_details.title == "":
            raise APIException(400)

        book_details.title = book_details.title.strip()

        if book_details.author:
            book_details.author = book_details.author.strip()

        if book_details.year is not None or book_details.year != 0:
            try:
                book_details.year = int(book_details.year)
            except ValueError:
                raise APIException(400)

        return book_details

    # --- Internal helpers ---

    @staticmethod
    def _extract_extension(csv_file: UploadFile) -> Optional[str]:
        filename = csv_file.filename.lower()
        return next((ext for ext in RouteValidator.allowed_extensions if filename.endswith(f".{ext}")), None)

    @staticmethod
    def _validate_file_type(ext: Optional[str]) -> None:
        if not ext:
            raise APIException(415)
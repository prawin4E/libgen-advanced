from fastapi import HTTPException

class APIException(HTTPException):
    ERROR_MESSAGES = {
        400: "Missing Params - The request is missing required parameters. Please ensure that all required fields are provided and try again to proceed with the processing",
        401: "Unauthorized - The request you made is not authorized. Please ensure that you have the necessary permissions to access the resource, and try again to proceed with the processing",
        404: "Resource Not Found - The resource you are trying to access could not be found. Please ensure that the book exists and that you have the correct identifier",
        406: "Not Acceptable - The request you made is not acceptable. Please ensure that the request meets the required criteria and try again to proceed with the processing",
        415: "File Format Not Supported - The file you uploaded is in an unsupported format. Please upload a file in a valid format, such as PDF, ensuring that it is neither corrupted nor incomplete for processing to proceed",
        422: "Corrupted or Damaged File - The document you uploaded appears to be corrupted or unreadable. Please upload a valid, non-corrupted file (e.g., PDF, DOC, or DOCX) that can be properly parsed.",
        500: "Unexpected Error - An unexpected error has occurred while processing your resume.",
        503: "Service Unavailable - A network issue has occurred that prevents the processing of your request. Please try again later, and if the problem persists, consider reaching out to technical support for further assistance"
    }

    def __init__(self, status_code: int):
        message = self.ERROR_MESSAGES.get(status_code, "Unknown Error")
        super().__init__(
            status_code=status_code,
            detail={
                "message": message,
                "status_code": status_code
            }
        )
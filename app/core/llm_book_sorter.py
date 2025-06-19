import boto3
from app.configs.appconf import env
from langchain_core.prompts import ChatPromptTemplate
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import PydanticOutputParser
from app.models.llm_output_models import BookSortOutput
from app.utils.logs import logger
from app.endpoints.errors import APIException


class LLMBookSorter:
    def __init__(self, csv_path: str, book_name: str):
        self.csv_path = csv_path
        self.book_name = book_name
        self.haiku = self._create_llm(env.MODEL_HAIKU)

    def _create_llm(self, MODEL_ID: str):
        return ChatBedrock(
            client=boto3.client("bedrock-runtime", region_name="us-east-1"),
            model_id=MODEL_ID,
            model_kwargs={"temperature": 0.2, "max_tokens": 3000}
        )
    
    def _build_prompt(self, parser: PydanticOutputParser):
        prompt = ChatPromptTemplate.from_template("""
You are a professional librarian AI. Your task is to sort a list of books based on the following criteria (in priority order):

1. **Relevance to the Title**: How closely the book aligns with the title provided.
2. **Quality**: Prefer well-known or authoritative works.
3. **Recentness**: Prefer newer editions or publication years.
4. **Book size**: Prefer books with:
    - Larger file size (in MB)
    - Higher page count (more pages)
    - If the page count is missing or zero, treat it as lower-quality or incomplete content.
5. **Author**:
    - If the author's name is provided, prefer books with known or reputable authors.
    - If author name is missing or unknown, infer author credibility based on other metadata.
6. **Language**: Prefer books in English (default), unless another language is explicitly needed.
7. **Year**: Use publication year to support recentness if not already covered.

---

You will be given:

- **Topic to sort by**:  
  `{context}`

- **List of books in CSV format** (each with title, size, pages, author, language, year, etc.):  
  `{books}`

---

{format_instructions}

**Important**:
- Only include books that are **PDFs**.
- Return **only** the JSON object as per the format instructions — no explanations, no extra text.
""").partial(format_instructions=parser.get_format_instructions())

        return prompt

    def _read_csv_file(self, csv_path):
        with open(csv_path, "r", encoding="utf-8") as file:
            return file.read()
        
    def sort(self) -> BookSortOutput:
        try:
            parser = PydanticOutputParser(pydantic_object=BookSortOutput)
            prompt = self._build_prompt(parser)
            formatted_prompt = prompt.format(
                context=self.book_name,
                books=self._read_csv_file(self.csv_path)
            )
            response = self.haiku.invoke(formatted_prompt)

            parsed_output = parser.parse(response.content)
            return parsed_output
        except Exception as e:
            logger.error(f"Error while classifying chunks: {str(e)}")
            raise APIException(500)
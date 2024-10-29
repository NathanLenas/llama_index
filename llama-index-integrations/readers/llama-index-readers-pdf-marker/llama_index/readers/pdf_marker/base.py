"""PDF Marker reader."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document


class PDFMarkerReader(BaseReader):
    """
    PDF Marker Reader. Reads a pdf to markdown format and tables with layout.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def load_data(
        self,
        file: Path,
        max_pages: int = None,
        langs: List[str] = None,
        batch_multiplier: int = 2,
        start_page: int = None,
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        """Load data from PDF
        Args:
            file (Path): Path for the PDF file.
            max_pages (int): is the maximum number of pages to process. Omit this to convert the entire document.
            langs (List[str]): List of languages to use for OCR. See supported languages : https://github.com/VikParuchuri/surya/blob/master/surya/languages.py
            batch_multiplier (int): is how much to multiply default batch sizes by if you have extra VRAM. Higher numbers will take more VRAM, but process faster. Set to 2 by default. The default batch sizes will take ~3GB of VRAM.
            start_page (int): Start page for conversion.

        Returns:
            List[Document]: List of documents.
        """
        from marker.convert import convert_single_pdf
        from marker.models import load_all_models
        from pypdf import PdfReader, PdfWriter

        try:
            pdf = PdfReader(str(file))

            inferred_langs = []
            if langs is None:
                if "EN" in file.name:
                    inferred_langs.append("English")
                if "DE" in file.name:
                    inferred_langs.append("German")
                if "FR" in file.name:
                    inferred_langs.append("French")
                if "LU" in file.name:
                    inferred_langs.append("English")
                    inferred_langs.append("French")
                    inferred_langs.append("German")
            #
            pages = []
            num_pages = len(pdf.pages)
            # create a new pdf for each page
            for i in range(num_pages):
                writer = PdfWriter()
                writer.add_page(pdf.pages[i])
                page_path = str(file).replace(".pdf", f"_{i}.pdf")
                pages.append({"path": page_path, "page_number": i + 1})
                writer.write(page_path)

            model_lst = load_all_models()

            docs = []
            for p in pages:
                try:
                    full_text, _, _ = convert_single_pdf(
                        p["path"],
                        model_lst,
                        max_pages=max_pages,
                        langs=langs if langs else inferred_langs,
                        batch_multiplier=batch_multiplier,
                        start_page=start_page,
                    )
                    if extra_info:
                        extra_info["title"] = Path(p["path"]).name
                        extra_info["page_number"] = p["page_number"]
                        docs.append(Document(text=full_text, extra_info=extra_info))
                    else:
                        extra_info = {
                            "title": p["path"].split("/")[-1],
                            "page_number": p["page_number"],
                        }
                except Exception as e:
                    # If an error occurs, continue to the next page
                    print(f"Error in processing page {p['page_number']}: {e}")
                    continue

            # remove the temporary files
            for p in pages:
                try:
                    Path(p["path"]).unlink()
                except:
                    continue
            return docs
            
        except Exception as e:
            print("Error processing " + str(file) +" : " + str(e))
            return []


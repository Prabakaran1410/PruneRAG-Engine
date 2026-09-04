from pathlib import Path
import fitz


def create_sample_pdf() -> None:
    directory = Path(__file__).parents[1] / "sample_data"
    for source in directory.glob("*.txt"):
        target = source.with_suffix(".pdf")
        document = fitz.open()
        page = document.new_page()
        rectangle = fitz.Rect(54, 54, 558, 738)
        current = ""
        for paragraph in source.read_text(encoding="utf-8").split("\n\n"):
            candidate = f"{current}\n\n{paragraph}".strip()
            if page.insert_textbox(rectangle, candidate, fontsize=11, lineheight=1.35) < 0:
                page = document.new_page()
                current = paragraph
                page.insert_textbox(rectangle, current, fontsize=11, lineheight=1.35)
            else:
                current = candidate
        document.save(target)
        print(target)


if __name__ == "__main__":
    create_sample_pdf()
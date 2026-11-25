import base64, io, zipfile
from pathlib import Path
MAX_BYTES=10*1024*1024
MAX_TEXT=24000

def read_file(name,raw):
    if len(raw)>MAX_BYTES: raise ValueError('File exceeds 10 MB')
    ext=Path(name).suffix.lower(); images=[]
    if ext=='.xlsx':
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries=archive.infolist()
            if len(entries)>1000 or sum(x.file_size for x in entries)>50*1024*1024:
                raise ValueError('Excel archive exceeds limits')
        from openpyxl import load_workbook
        book=load_workbook(io.BytesIO(raw),read_only=True,data_only=True)
        try:
            lines=[]
            if len(book.sheetnames)>10: raise ValueError("Too many sheets")
            for sheet in book:
                if (sheet.max_column or 0)>100: raise ValueError("Too many columns")
                lines.append(sheet.title)
                for i,row in enumerate(sheet.values):
                    if i>=500: raise ValueError('Maximum 500 rows per sheet')
                    lines.append(' | '.join(str(v or '') for v in row))
            text='\n'.join(lines)
        finally: book.close()
    elif ext=='.pdf':
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw))
        if len(reader.pages)>20: raise ValueError('Maximum 20 PDF pages')
        text='\n'.join(p.extract_text() or '' for p in reader.pages)
        if not text.strip():
            import pypdfium2 as pdfium
            doc=pdfium.PdfDocument(raw)
            if len(doc)>3: raise ValueError('Scanned PDF: maximum 3 pages')
            try:
                for page in doc:
                    try:
                        w,h=page.get_size()
                        if min(w,h)<=0 or max(w,h)>10000: raise ValueError('Invalid PDF page size')
                        img=page.render(scale=min(1.5,1400/max(w,h))).to_pil(); images.append(encode_image(img))
                    finally: page.close()
            finally: doc.close()
    elif ext in {'.png','.jpg','.jpeg','.webp'}:
        from PIL import Image
        with Image.open(io.BytesIO(raw)) as img: images=[encode_image(img)]
        text=''
    else: raise ValueError('Unsupported file type')
    if len(text)>MAX_TEXT: raise ValueError('Extracted text exceeds limit')
    return text,images

def encode_image(img):
    if img.width*img.height>16000000: raise ValueError("Image exceeds pixel limit")
    img.thumbnail((1400,1400)); out=io.BytesIO(); img.convert('RGB').save(out,format='JPEG',quality=80)
    return 'data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()

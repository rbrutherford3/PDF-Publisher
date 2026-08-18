from flask import Flask, render_template, request, send_file, send_from_directory
from io import BytesIO
import os
import shutil
import tempfile
import PyPDF2
from fpdf import FPDF
from cloudconvert_service import CloudConvertError, convert_office_to_pdf, resolve_api_key
from turnstile import SITE_KEY

app = Flask(__name__)
WORK_DIR = os.environ.get("PDFPUBLISHER_WORK_DIR") or os.path.join(tempfile.gettempdir(), "pdfpublisher")
os.makedirs(WORK_DIR, exist_ok=True)


def get_output_path(filename: str) -> str:
    return os.path.join(WORK_DIR, filename)


def get_uploads_dir() -> str:
    uploads_dir = os.path.join(WORK_DIR, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    return uploads_dir

# If the deployment needs to serve the app from the /pdfpublisher/ subdirectory,
# restore the redirect below by uncommenting it and updating the route decorators
# accordingly.
# from flask import redirect
# @app.route("/")
# def root():
#     return redirect("/pdfpublisher/")

# Serve the upload page directly at the site root
@app.route("/", methods=["GET"])
def root():
    return upload()


@app.route("/health")
def health():
    return "ok", 200


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.static_folder, "favicon"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/site.webmanifest")
def webmanifest():
    return send_from_directory(
        os.path.join(app.static_folder, "favicon"),
        "site.webmanifest",
        mimetype="application/manifest+json",
    )


@app.route("/cloudconvert/test")
def cloudconvert_test_page():
    return render_template(
        "cloudconvert_test.html",
        api_key_value=resolve_api_key(),
        error_message=None,
    )


@app.route("/cloudconvert/test", methods=["POST"])
def cloudconvert_test_convert():
    uploaded_file = request.files.get("file")
    api_key = (request.form.get("api_key") or resolve_api_key() or "").strip()

    if uploaded_file is None or not uploaded_file.filename:
        return render_template(
            "cloudconvert_test.html",
            api_key_value=api_key,
            error_message="Choose a .doc, .docx, or .odt file to convert.",
        )

    try:
        pdf_bytes, output_filename = convert_office_to_pdf(uploaded_file, api_key)
    except CloudConvertError as exc:
        return render_template(
            "cloudconvert_test.html",
            api_key_value=api_key,
            error_message=str(exc),
        )

    return send_file(
        BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=output_filename,
    )

# Page numbering class taken from https://stackoverflow.com/a/68382694/3130769
class NumberPDF(FPDF):
    def __init__(self, numberOfPages: int, pagenumberformat: int, pagenumberfont: str, pagenumbersize: int, pagenumbermargin: float):
        super().__init__("P", "in", "Letter")
        self.numberOfPages = numberOfPages
        self.pagenumberformat = pagenumberformat
        self.pagenumberfont = pagenumberfont
        self.pagenumbersize = pagenumbersize
        self.pagenumbermargin = pagenumbermargin

    # Overload Header
    def header(self):
        pass

    # Overload Footer
    def footer(self):
        self.set_y(-self.pagenumbermargin)
        self.set_font(self.pagenumberfont, '', self.pagenumbersize)
        if self.pagenumberformat == 1:
            self.cell(0, 0, f"{self.page_no()}", 0, 0, 'C')
        elif self.pagenumberformat == 2:
            self.cell(0, 0, f"{self.page_no()} of {self.numberOfPages}", 0, 0, 'C')
        elif self.pagenumberformat == 3:
            self.cell(0, 0, f"Page {self.page_no()}", 0, 0, 'C')
        else:
            self.cell(0, 0, f"Page {self.page_no()} of {self.numberOfPages}", 0, 0, 'C')
        

# Go to file upload initially
# The former /pdfpublisher/ subpath is intentionally disabled; the root route
# above continues to serve the upload page.
# @app.route("/pdfpublisher/")
def upload():
    return render_template("upload.html", turnstile_site_key=SITE_KEY, error_message=None)

@app.route('/', methods=['POST'])
def success():
    uploads = get_uploads_dir()
    result = get_output_path("result.pdf")
    # Get rid of old result, if it exist
    if os.path.exists(result):
        os.remove(result)
    # Create uploads folder if it doesn't exist:
    if not os.path.exists(uploads):
        os.makedirs(uploads, exist_ok=True)
    else:
        # Get ride of old uploads, if they exist
        oldfiles = os.listdir(uploads)
        for f in oldfiles:
            os.remove(os.path.join(uploads, f))
    # Save each .docx, convert to .pdf, delete .docx
    filelist = request.files.getlist("file")
    justnames = []
    for f in filelist:
        if not f.filename:
            continue
        filename, extension = os.path.splitext(f.filename)
        extension = extension.lower()
        justnames.append(filename)
        if extension in {".doc", ".docx", ".odt"}:
            api_key = resolve_api_key()
            try:
                pdf_bytes, _ = convert_office_to_pdf(f, api_key=api_key, filename=f.filename)
                output_pdf_path = os.path.join(uploads, f"{filename}.pdf")
                with open(output_pdf_path, "wb") as output_pdf:
                    output_pdf.write(pdf_bytes)
            except CloudConvertError as exc:
                message = f"CloudConvert conversion failed for {f.filename}: {exc}"
                print(message)
                return render_template("upload.html", turnstile_site_key=SITE_KEY, error_message=message)
        else:
            f.save(os.path.join(uploads, f.filename))
    # Send bare filenames to 'arrange.html' for ordering
    return render_template("arrange.html", pdfs = justnames, pdfslen = len(justnames))

# Gather .pdf documents, create page numbers and table of contents, and merge
@app.route('/pdfpublisher/compile', methods = ['POST'])
def compile():
    parameters = request.form
    work_dir = WORK_DIR
    uploads = get_uploads_dir()

    # Remove previous .pdf files from the app working directory
    for filename in os.listdir(work_dir):
        if filename.lower().endswith("pdf"):
            os.remove(os.path.join(work_dir, filename))

    # Define pdf filenames
    unindexedfile = get_output_path("unindexed.pdf")
    indexedfile = get_output_path("indexed.pdf")
    indexedfilewithtoc = get_output_path("indexed_toc.pdf")
    tocfile = get_output_path("contents.pdf")
    final = get_output_path("final.pdf")
    finaloutlined = get_output_path("final_out.pdf")

    # Gather filenames in user-specified order and user-specified titles
    filenames = request.form.get("finalorder")
    titles = request.form.get("titles")
    filelist = filenames.split('$') if filenames else []
    titlelist = titles.split('$') if titles else []

    # Get page numbering 
    pagenumbers = request.form.get("pagenumbers")
    numberingstart = None
    if pagenumbers:
        pagenumberformat = int(request.form.get("pagenumberformat", 1))
        pagenumberfont = request.form.get("pagenumberfont", "Arial")
        pagenumbersize = int(request.form.get("pagenumbersize", 12))
        pagenumbermargin = float(request.form.get("pagenumbermargin", 0.5))
        numberingstart = request.form.get("numberingstart")

    # Create merge object, define initial conditions
    indexedresult = PyPDF2.PdfMerger()
    unindexedresult = PyPDF2.PdfMerger()
    tocpagenumber = 1
    tocnumpages = 0
    toclist = ""
    toc = request.form.get("toc")
    if toc:
        # Gather user-defined length and size criteria
        tocheaderfont = request.form.get("tocheaderfont", "Arial")
        tocheadersize = int(request.form.get("tocheadersize", 18))
        tocheaderspacing = float(request.form.get("tocheaderspacing", 0.5))
        toclistitemfont = request.form.get("toclistitemfont", "Arial")
        toclistitemsize = int(request.form.get("toclistitemsize", 12))
        tocverticalmargin = float(request.form.get("tocverticalmargin", 1))
        tochorizontalmargin = float(request.form.get("tochorizontalmargin", 1))
        cellwidth = (8.5-2*tochorizontalmargin)   # 8.5 inches minus twice the horizontal margin
        toclistitemspacing = float(request.form.get("toclistitemspacing", 0.25))

        # Do T.O.C. dry-run to get T.O.C. number of pages (necessary if T.O.C. is counted with page numbers)
        y = tocverticalmargin
        tocpassed = False
        tocnumpages += 1
        beginnumbering = False
        
        y += tocheaderspacing
        for i in range(len(filelist)):
            if filelist[i] == numberingstart:
                beginnumbering = True
            if filelist[i] == "### TABLE OF CONTENTS ###":
                tocpassed = True
            else:
                pdf = PyPDF2.PdfReader(os.path.join(uploads, filelist[i]))
                if beginnumbering:
                    if tocpassed:
                        y += toclistitemspacing
                        # Continue table of contents onto another page if no more room
                        if y > 11 - tocverticalmargin:
                            tocnumpages += 1 # Add page number for bookmarks
                            y = tocverticalmargin

        # Create table of contents page
        contents = FPDF("P", "in", "Letter")
        contents.set_auto_page_break(False)
        contents.add_page()

        # Create table of contents header
        contents.set_font(tocheaderfont, '', tocheadersize)
        y = tocverticalmargin
        contents.set_xy(tochorizontalmargin, y)
        contents.cell(cellwidth, 0, "Table of Contents", 0, 0, "C")
        tocpassed = False
        beginnumbering = False

        # Loop through each item in the list of documents and add them to the T.O.C.
        y += tocheaderspacing
        contents.set_font(toclistitemfont, '', toclistitemsize)
        for i in range(len(filelist)):
            if filelist[i] == numberingstart:
                beginnumbering = True
            if filelist[i] == "### TABLE OF CONTENTS ###":
                tocpassed = True
                if beginnumbering:
                    tocpagenumber += tocnumpages
            else:
                pdf = PyPDF2.PdfReader(os.path.join(uploads, filelist[i]))
                if beginnumbering:
                    if tocpassed:
                        contents.set_xy(tochorizontalmargin, y)
                        contents.cell(cellwidth, 0, titlelist[i], 0, 0, 'L')
                        contents.set_xy(tochorizontalmargin, y)
                        contents.cell(cellwidth, 0, str(tocpagenumber), 0, 0, 'R')
                        y += toclistitemspacing
                        # Continue table of contents onto another page if no more room
                        if y > 11 - tocverticalmargin:
                            contents.add_page()
                            y = tocverticalmargin
                    tocpagenumber += len(pdf.pages)
        contents.output(tocfile)    # Save the T.O.C. file for later
    
    # Create bookmarks in PDF file and assemble PDFs
    beginnumbering = False
    unindexedempty = True
    pagenumber = 1
    for i in range(len(filelist)):
        if filelist[i] == numberingstart:
            beginnumbering = True
        if filelist[i] == "### TABLE OF CONTENTS ###":
            pdffile = tocfile
            toclist += "\"Table of Contents\" " + str(pagenumber) + "\n"
        else:
            pdffile = os.path.join(uploads, filelist[i])
            toclist += "\"" + titlelist[i] + "\" " + str(pagenumber) + "\n"
        if beginnumbering:
            indexedresult.append(pdffile)
        else:
            unindexedempty = False
            unindexedresult.append(pdffile)
        pdf = PyPDF2.PdfReader(pdffile)
        pagenumber += len(pdf.pages)

    # Save the table of contents pdf bookmark list for later
    f = open(get_output_path("toc"), "w")
    f.write(toclist)
    f.close()

    # Save the merged files
    if not unindexedempty:
        unindexedresult.write(unindexedfile)
        unindexedresult.close()
    indexedresult.write(indexedfile)
    indexedresult.close()

    # Delete the individual pdfs
    upload_files = os.listdir(uploads)
    for f in upload_files:
        os.remove(os.path.join(uploads, f))
    
    if pagenumbers:
        # Page numbering code taken from https://stackoverflow.com/a/68382694/3130769
        original = get_output_path("originalresult.pdf")
        os.rename(indexedfile, original)
        # Grab the file you want to add pages to
        inputFile = PyPDF2.PdfReader(original)

        # Create a temporary numbering PDF using the overloaded FPDF class, passing the number of pages
        # from your original file
        numpages = len(inputFile.pages)
        tempNumFile = NumberPDF(numpages, pagenumberformat, pagenumberfont, pagenumbersize, pagenumbermargin)

        # Add a new page to the temporary numbering PDF (the footer function runs on add_page and will 
        # put the page number at the bottom, all else will be blank
        for page in range(len(inputFile.pages)):
            tempNumFile.add_page()

        # Save the temporary numbering PDF
        tempNumFile.output(get_output_path("tempNumbering.pdf"))

        # Create a new PDFFileReader for the temporary numbering PDF
        mergeFile = PyPDF2.PdfReader(get_output_path("tempNumbering.pdf"))

        # Create a new PDFFileWriter for the final output document
        mergeWriter = PyPDF2.PdfWriter()

        # Loop through the pages in the temporary numbering PDF
        for page_idx, page in enumerate(mergeFile.pages):
            # Grab the corresponding page from the inputFile
            inputPage = inputFile.pages[page_idx]
            # Merge the inputFile page and the temporary numbering page
            inputPage.merge_page(page)
            # Add the merged page to the final output writer
            mergeWriter.add_page(inputPage)

        # Delete the temporary file and the input file
        os.remove(original)
        os.remove(get_output_path("tempNumbering.pdf"))

        # Write the merged output
        with open(indexedfile, 'wb') as fh:
            mergeWriter.write(fh)

    # Compile the pdf
    if unindexedempty:
        os.rename(indexedfile, final)
    else:
        result = PyPDF2.PdfMerger()
        result.append(unindexedfile)
        result.append(indexedfile)
        result.write(final)
        result.close()
        os.remove(unindexedfile)
        os.remove(indexedfile)

    # Create a pdf file with the table of contents bookmarks
    toc_path = get_output_path("toc")
    if shutil.which("pdftocio"):
        os.system(f"export PATH=$PATH:/usr/local/bin; pdftocio {final} < {toc_path}")
        os.remove(toc_path)
        os.remove(final)
        os.rename(finaloutlined, final)
    else:
        # pdftocio not available, skip bookmark creation but keep the PDF
        if os.path.exists(toc_path):
            os.remove(toc_path)
        if os.path.exists(finaloutlined):
            os.remove(finaloutlined)

    # Download the final result
    return send_file(final, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

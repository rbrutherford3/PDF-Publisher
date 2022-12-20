from flask import *
import os
import PyPDF2
from fpdf import FPDF
from recaptchav3 import reCAPTCHAv3
import requests

app = Flask(__name__)

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
@app.route("/pdfpublisher/")
def upload():
    return render_template("upload.html", reCAPTCHA_site_key=reCAPTCHAv3.site_key)

@app.route('/pdfpublisher/success', methods = ['POST'])
def success():
    uploads = "uploads"
    result = "result.pdf"
    if request.method == 'POST':
        parameters = request.form
        recaptcha_passed = False
        recaptcha_response = parameters.get('g-recaptcha-response')
        try:
            recaptcha_secret = reCAPTCHAv3.secret_key
            response = requests.post(f'https://www.google.com/recaptcha/api/siteverify?secret={recaptcha_secret}&response={recaptcha_response}').json()
            recaptcha_passed = response.get('success')
        except Exception as e:
            print(f"failed to get reCaptcha: {e}")
        if recaptcha_passed:
            # Get rid of old result, if it exist
            if os.path.exists(result):
                os.remove(result)
            # Create uploads folder if it doesn't exist:
            if not os.path.exists(uploads):
                os.mkdir(uploads)
            else:
                # Get ride of old uploads, if they exist
                oldfiles = os.listdir(uploads)
                for f in oldfiles:
                    os.remove(os.path.join(uploads, f))
            # Save each .docx, convert to .pdf, delete .docx
            filelist = request.files.getlist("file")
            justnames = []
            for f in filelist:
                filename, extension = os.path.splitext(f.filename)
                justnames.append(filename)
                f.save(os.path.join(uploads, f.filename))
                if extension == ".doc" or extension == ".docx" or extension == ".odt":
                    os.system("export PATH=$PATH:/usr/bin; libreoffice --headless --convert-to pdf '" + uploads + "/" + f.filename + "' --outdir " + uploads)
                    os.remove(os.path.join(uploads, f.filename))
            justnames.append("TABLE OF CONTENTS")
            justnames.reverse()
            # Send bare filenames to 'arrange.html' for ordering
            return render_template("arrange.html", pdfs = justnames, pdfslen = len(justnames))
        else:
            return "Homosapiens only, please!"

# Gather .pdf documents, create page numbers and table of contents, and merge
@app.route('/pdfpublisher/compile', methods = ['POST'])
def compile():
    parameters = request.form
    # Remove previous .pdf files
    for filename in os.listdir(os.getcwd()):
        if filename.lower().endswith("pdf"):
            os.remove(filename)
    
    # Define pdf filenames
    unindexedfile = "unindexed.pdf"
    indexedfile = "indexed.pdf"
    indexedfilewithtoc = "indexed_toc.pdf"
    tocfile = "contents.pdf"
    final = "final.pdf"
    finaloutlined = "final_out.pdf"

    # Gather filenames in user-specified order and user-specified titles
    filenames = request.form.get("finalorder")
    titles = request.form.get("titles")
    filelist = filenames.split('$')
    titlelist = titles.split('$')

    # Create merge object, define initial conditions
    indexedresult = PyPDF2.PdfMerger()
    unindexedresult = PyPDF2.PdfMerger()
    tocpagenumber = 1
    tocnumpages = 0
    toclist = ""
    toc = request.form.get("toc")
    if toc:
        # Gather user-defined length and size criteria
        tocheaderfont = request.form.get("tocheaderfont")
        tocheadersize = int(request.form.get("tocheadersize"))
        tocheaderspacing = float(request.form.get("tocheaderspacing"))
        toclistitemfont = request.form.get("toclistitemfont")
        toclistitemsize = int(request.form.get("toclistitemsize"))
        tocverticalmargin = float(request.form.get("tocverticalmargin"))
        tochorizontalmargin = float(request.form.get("tochorizontalmargin"))
        cellwidth = (8.5-2*tochorizontalmargin)   # 8.5 inches minus twice the horizontal margin
        toclistitemspacing = float(request.form.get("toclistitemspacing"))

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
        tocnumpages += 1

        # Loop through each item in the list of documents and add them to the T.O.C.
        y += tocheaderspacing
        contents.set_font(toclistitemfont, '', toclistitemsize)
        for i in range(len(filelist)):
            if filelist[i] == "### TABLE OF CONTENTS ###":
                tocpassed = True
            else:
                pdf = PyPDF2.PdfFileReader("uploads/" + filelist[i])
                if tocpassed:
                    contents.set_xy(tochorizontalmargin, y)
                    contents.cell(cellwidth, 0, titlelist[i], 0, 0, 'L')
                    contents.set_xy(tochorizontalmargin, y)
                    contents.cell(cellwidth, 0, str(tocpagenumber), 0, 0, 'R')
                    y += toclistitemspacing
                    tocpagenumber += pdf.getNumPages()
                    # Continue table of contents onto another page if no more room
                    if y > 11 - tocverticalmargin:
                        contents.add_page()
                        tocnumpages += 1 # Add page number for bookmarks
                        y = tocverticalmargin
        contents.output(tocfile)    # Save the T.O.C. file for later
    
    # Create bookmarks in PDF file and assemble PDFs
    tocpassed = False
    unindexedempty = True
    pagenumber = 1
    for i in range(len(filelist)):
        if filelist[i] == "### TABLE OF CONTENTS ###":
            tocpassed = True
            pagenumber += tocnumpages
        else:
            pdf = PyPDF2.PdfFileReader("uploads/" + filelist[i])
            if tocpassed:              
                toclist += "\"" + titlelist[i] + "\"" + " " + str(pagenumber) + "\n"
                indexedresult.append("uploads/" + filelist[i])
            else:
                unindexedempty = False
                unindexedresult.append("uploads/" + filelist[i])
            pagenumber += pdf.getNumPages()

    # Save the table of contents pdf bookmark list for later
    f = open("toc", "w")
    f.write(toclist)
    f.close()

    # Save the merged files
    if not unindexedempty:
        unindexedresult.write(unindexedfile)
        unindexedresult.close()
    indexedresult.write(indexedfile)
    indexedresult.close()

    # Delete the individual pdfs
    uploads = os.listdir("uploads")
    for f in uploads:
        os.remove(os.path.join("uploads", f))
    
    if request.form.get("pagenumbers"):
        # Page numbering code taken from https://stackoverflow.com/a/68382694/3130769
        original = "originalresult.pdf"
        os.rename(indexedfile, original)
        # Grab the file you want to add pages to
        inputFile = PyPDF2.PdfFileReader(original)

        # Create a temporary numbering PDF using the overloaded FPDF class, passing the number of pages
        # from your original file
        numpages = inputFile.getNumPages()
        pagenumberformat = int(request.form.get("pagenumberformat"))
        pagenumberfont = request.form.get("pagenumberfont")
        pagenumbersize = int(request.form.get("pagenumbersize"))
        pagenumbermargin = float(request.form.get("pagenumbermargin"))
        tempNumFile = NumberPDF(numpages, pagenumberformat, pagenumberfont, pagenumbersize, pagenumbermargin)

        # Add a new page to the temporary numbering PDF (the footer function runs on add_page and will 
        # put the page number at the bottom, all else will be blank
        for page in range(inputFile.getNumPages()):
            tempNumFile.add_page()

        # Save the temporary numbering PDF
        tempNumFile.output("tempNumbering.pdf")

        # Create a new PDFFileReader for the temporary numbering PDF
        mergeFile = PyPDF2.PdfFileReader("tempNumbering.pdf")

        # Create a new PDFFileWriter for the final output document
        mergeWriter = PyPDF2.PdfFileWriter()

        # Loop through the pages in the temporary numbering PDF
        for pagenumbersize, page in enumerate(mergeFile.pages):
            # Grab the corresponding page from the inputFile
            inputPage = inputFile.getPage(pagenumbersize)
            # Merge the inputFile page and the temporary numbering page
            inputPage.mergePage(page)
            # Add the merged page to the final output writer
            mergeWriter.addPage(inputPage)

        # Delete the temporary file and the input file
        os.remove(original)
        os.remove("tempNumbering.pdf")

        # Write the merged output
        with open(indexedfile, 'wb') as fh:
            mergeWriter.write(fh)

    # Compile table of contents with the pdf
    if toc:
        result = PyPDF2.PdfMerger()
        result.append(tocfile)
        result.append(indexedfile)
        result.write(indexedfilewithtoc)
        result.close()
        os.remove(tocfile)
        os.remove(indexedfile)
        # Add non-indexed files, if applicable:
        if unindexedempty:
            os.rename(indexedfilewithtoc, final)
        else:
            result = PyPDF2.PdfMerger()
            result.append(unindexedfile)
            result.append(indexedfilewithtoc)
            result.write(final)
            result.close()
            os.remove(unindexedfile)
            os.remove(indexedfilewithtoc)
    else:
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
    os.system("export PATH=$PATH:/usr/local/bin; pdftocio " + final + " < toc")
    os.remove("toc")
    os.remove(final)
    os.rename(finaloutlined, final)

    # Download the final result
    return send_file(final, as_attachment=True)

if __name__ == "__main__":
    app.run()

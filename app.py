from flask import *
import os
import PyPDF2
from fpdf import FPDF

app = Flask(__name__)

# Page numbering class taken from https://stackoverflow.com/a/68382694/3130769
class NumberPDF(FPDF):
    def __init__(self, numberOfPages: int, pagenumberformat: int, pagenumberfont: str, pagenumbersize: int, pagenumbermargin: float):
        super(NumberPDF, self).__init__()
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
        self.set_y(-self.pagenumbermargin*25.4) # Convert from inches to millimeters
        self.set_font(self.pagenumberfont, '', self.pagenumbersize)
        if self.pagenumberformat == 1:
            self.cell(0, 10, f"{self.page_no()}", 0, 0, 'C')
        elif self.pagenumberformat == 2:
            self.cell(0, 10, f"{self.page_no()} of {self.numberOfPages}", 0, 0, 'C')
        elif self.pagenumberformat == 3:
            self.cell(0, 10, f"Page {self.page_no()}", 0, 0, 'C')
        else:
            self.cell(0, 10, f"Page {self.page_no()} of {self.numberOfPages}", 0, 0, 'C')
        

# Go to file upload initially
@app.route("/")
def upload():
    return render_template("upload.html")

@app.route('/success', methods = ['POST'])
def success():
    uploads = "uploads"
    result = "result.pdf"
    if request.method == 'POST':
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
            if extension == ".doc" or extension == ".docx":
                os.system("export PATH=$PATH:/usr/bin; libreoffice --headless --convert-to pdf '" + uploads + "/" + f.filename + "' --outdir " + uploads)
                os.remove(os.path.join(uploads, f.filename))
        justnames.reverse()
        # Send bare filenames to 'arrange.html' for ordering
        return render_template("arrange.html", pdfs = justnames, pdfslen = len(justnames))

# Gather .pdf documents, create page numbers and table of contents, and merge
@app.route('/compile', methods = ['POST'])
def compile():
        # Remove previous .pdf files
        for filename in os.listdir(os.getcwd()):
            if filename.lower().endswith("pdf"):
                os.remove(filename)
        
        # Define pdf filenames
        result = "result.pdf"
        result_outlined = "result_out.pdf"
        tocfile = "contents.pdf"
        final = "final.pdf"

        # Gather filenames in user-specified order and user-specified titles
        filenames = request.form.get("finalorder")
        titles = request.form.get("titles")
        filelist = filenames.split('$')
        titlelist = titles.split('$')

        # Create merge object, define initial conditions
        merger = PyPDF2.PdfMerger()
        pagenumber = 1
        toclist = ""
        toc = request.form.get("toc")
        if toc:
            # Gather user-defined length and size criteria
            tocheaderfont = request.form.get("tocheaderfont")
            tocheadersize = int(request.form.get("tocheadersize"))
            tocheaderspacing = 25.4*float(request.form.get("tocheaderspacing")) # Converted to mm
            toclistitemfont = request.form.get("toclistitemfont")
            toclistitemsize = int(request.form.get("toclistitemsize"))
            tocverticalmargin = 25.4*float(request.form.get("tocverticalmargin")) # Converted to mm
            tochorizontalmargin = 25.4*float(request.form.get("tochorizontalmargin")) # Converted to mm
            cellwidth = (215.9-2*tochorizontalmargin)   # 8.5 inches minus twice the horizontal margin
            toclistitemspacing = 25.4*float(request.form.get("toclistitemspacing")) #Converted to mm

            # Create table of contents page
            contents = FPDF()
            contents.add_page()

            # Create table of contents header
            contents.set_font(tocheaderfont, '', tocheadersize)
            y = tocverticalmargin
            contents.set_xy(tochorizontalmargin, y)
            contents.cell(cellwidth, 0, "Table of Contents", 0, 0, "C")

            # Loop through each item in the list of documents and add them to the T.O.C.
            # and create the T.O.C. PDF bookmarks and merge the documents into one PDF
            y += tocheaderspacing
            contents.set_font(toclistitemfont, '', toclistitemsize)
            for i in range(len(filelist)):
                pdf = PyPDF2.PdfFileReader("uploads/" + filelist[i])
                toclist += "\"" + titlelist[i] + "\"" + " " + str(pagenumber) + "\n"
                contents.set_xy(tochorizontalmargin, y)
                contents.cell(cellwidth, 0, titlelist[i], 0, 0, 'L')
                contents.set_xy(tochorizontalmargin, y)
                contents.cell(cellwidth, 0, str(pagenumber), 0, 0, 'R')
                y += toclistitemspacing
                pagenumber += pdf.getNumPages()
                merger.append("uploads/" + filelist[i])
            contents.output(tocfile)    # Save the T.O.C. file for later
        else:
            # If not making a T.O.C. page, simply merge the documents and make the
            # T.O.C. file for creating the PDF bookmarks later
            for i in range(len(filelist)):
                pdf = PyPDF2.PdfFileReader("uploads/" + filelist[i])
                toclist += "\"" + titlelist[i] + "\"" + " " + str(pagenumber) + "\n"
                pagenumber += pdf.getNumPages()
                merger.append("uploads/" + filelist[i])
        # Save the table of contents pdf bookmark list for later
        f = open("toc", "w")
        f.write(toclist)
        f.close()

        # Save the merged file
        merger.write(result)
        merger.close()

        # Delete the individual pdfs
        uploads = os.listdir("uploads")
        for f in uploads:
            os.remove(os.path.join("uploads", f))
        
        if request.form.get("pagenumbers"):
            # Page numbering code taken from https://stackoverflow.com/a/68382694/3130769
            original = "originalresult.pdf"
            os.rename(result, original)
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
            with open(result, 'wb') as fh:
                mergeWriter.write(fh)
        
        # Create a pdf file with the table of contents bookmarks
        os.system("export PATH=$PATH:/usr/local/bin; pdftocio " + result + " < toc")
        os.remove("toc")
        os.remove(result)

        # Compile table of contents with the pdf
        if toc:
            merger = PyPDF2.PdfMerger()
            merger.append(tocfile)
            merger.append(result_outlined)
            merger.write(final)
            merger.close()
            os.remove(tocfile)
        else:
            os.rename(result_outlined, final)

        # Download the final result
        return send_file(final, as_attachment=True)

if __name__ == "__main__":
    app.run()
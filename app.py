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
            docx = f.filename
            justname = docx.replace(".docx", "")
            justnames.append(justname)
            f.save(os.path.join(uploads, docx))
            os.system("export PATH=$PATH:/usr/bin; libreoffice --headless --convert-to pdf '" + uploads + "/" + docx + "' --outdir " + uploads)
            os.remove(os.path.join(uploads, docx))
        justnames.reverse()
        # Send bare filenames to 'arrange.html' for ordering
        return render_template("arrange.html", pdfs = justnames, pdfslen = len(justnames))

# Gather .pdf documents, create page numbers and table of contents, and merge
@app.route('/compile', methods = ['POST'])
def compile():
        result = "result.pdf"
        result_outlined = "result_out.pdf"
        if os.path.exists(result_outlined):
            os.remove(result_outlined)
        filenames = request.form['finalorder']
        titles = request.form['titles']
        filelist = filenames.split('$')
        titlelist = titles.split('$')
        merger = PyPDF2.PdfMerger()
        pagenumber = 1
        toc = ""
        contents = FPDF('P','in','Letter')
        contents.add_page()
        contents.set_font('Arial', '', 12)
        pagenumbersize = 10
        pagenumbermargin = 10
        for i in range(len(filelist)):
            pdf = PyPDF2.PdfFileReader("uploads/" + filelist[i])
            toc += "\"" + titlelist[i] + "\"" + " " + str(pagenumber) + "\n"
            contents.set_xy(pagenumbersize, pagenumbermargin)
            contents.cell(195.9, 0, titlelist[i], 0, 0, 'L')
            contents.set_xy(pagenumbersize, pagenumbermargin)
            contents.cell(195.9, 0, str(pagenumber), 0, 0, 'R')
            pagenumbermargin += 10
            pagenumber += pdf.getNumPages()
            merger.append("uploads/" + filelist[i])
        contents.output("contents.pdf")
        f = open("toc", "w")
        f.write(toc)
        f.close()
        merger.write(result)
        merger.close()
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
        
        os.system("export PATH=$PATH:/usr/local/bin; pdftocio " + result + " < toc")
        os.remove("toc")
        os.remove(result)
        return send_file(result_outlined, as_attachment=True)      

if __name__ == "__main__":
    app.run()
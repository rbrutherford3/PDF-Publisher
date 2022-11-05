from flask import *
import os
import PyPDF2
from fpdf import FPDF

app = Flask(__name__)

# Page numbering class taken from https://stackoverflow.com/a/68382694/3130769
class NumberPDF(FPDF):
    def __init__(self, numberOfPages, pagenumberfont, pagenumbersize):
        super(NumberPDF, self).__init__()
        self.numberOfPages = numberOfPages
        self.pagenumberfont = pagenumberfont
        self.pagenumbersize = pagenumbersize

    # Overload Header
    def header(self):
        pass

    # Overload Footer
    def footer(self):
        self.set_y(-15)
        self.set_font(self.pagenumberfont, '', self.pagenumbersize)
        self.cell(0, 10, f"{self.page_no()}", 0, 0, 'C')

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

@app.route('/compile', methods = ['POST'])
def compile():
        result = "result.pdf"
        filenames = request.form['finalorder']
        filelist = filenames.split('$')
        merger = PyPDF2.PdfMerger()
        for f in filelist:
            merger.append("uploads/" + f)
        merger.write(result)
        merger.close()
        uploads = os.listdir("uploads")
        for f in uploads:
            os.remove(os.path.join("uploads", f))  
        
        if request.form.get("pagenumbers"):
            # Page numbering code taken from https://stackoverflow.com/a/68382694/3130769

            # Grab the file you want to add pages to
            inputFile = PyPDF2.PdfFileReader(result)
            outputFile = "resultWithPageNumbers.pdf"

            # Create a temporary numbering PDF using the overloaded FPDF class, passing the number of pages
            # from your original file
            tempNumFile = NumberPDF(inputFile.getNumPages(), request.form.get("pagenumberfont"), int(request.form.get("pagenumbersize")))

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
            for x, page in enumerate(mergeFile.pages):
                # Grab the corresponding page from the inputFile
                inputPage = inputFile.getPage(x)
                # Merge the inputFile page and the temporary numbering page
                inputPage.mergePage(page)
                # Add the merged page to the final output writer
                mergeWriter.addPage(inputPage)

            # Delete the temporary file and the input file
            os.remove(result)
            os.remove("tempNumbering.pdf")

            # Write the merged output
            with open(outputFile, 'wb') as fh:
                mergeWriter.write(fh)

            # Download the result
            return send_file(outputFile, as_attachment=True)
        else:
            return send_file(result, as_attachment=True)          

if __name__ == "__main__":
    app.run()
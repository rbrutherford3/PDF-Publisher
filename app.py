from flask import *
import os
from PyPDF2 import PdfMerger
app = Flask(__name__)

# Go to file upload initially
@app.route("/")
def upload():
    return render_template("upload.html")

@app.route('/success', methods = ['POST'])
def success():
    if request.method == 'POST':
        # Get rid of old result, if it exist
        if os.path.exists("result.pdf"):
            os.remove("result.pdf")
        # Create uploads folder if it doesn't exist:
        if not os.path.exists("uploads"):
            os.mkdir("uploads")
        else:
            # Get ride of old uploads, if they exist
            oldfiles = os.listdir("uploads")
            for f in oldfiles:
                os.remove(os.path.join("uploads", f))
        # Save each .docx, convert to .pdf, delete .docx
        filelist = request.files.getlist("file")
        justnames = []
        for f in filelist:
            docx = f.filename
            justname = docx.replace(".docx", "")
            justnames.append(justname)
            f.save("uploads/" + docx)
            os.system("libreoffice --headless --convert-to pdf 'uploads/" + docx + "' --outdir uploads")
            os.remove("uploads/" + docx)
        justnames.reverse()
        # Send bare filenames to 'arrange.html' for ordering
        return render_template("arrange.html", pdfs = justnames, pdfslen = len(justnames))

@app.route('/compile', methods = ['POST'])
def compile():
        filenames = request.form['finalorder']
        filelist = filenames.split('$')
        merger = PdfMerger()
        for f in filelist:
            merger.append("uploads/" + f)
        merger.write("result.pdf")
        merger.close()
        path = "result.pdf"
        return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run()

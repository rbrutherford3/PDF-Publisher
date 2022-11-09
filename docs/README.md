# docx Publisher

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

This is a Flask app that takes uploaded .docx files, converts them to .pdf, allows the user to arrange the files to suit them, and then merges them into one big file.  Future versions will include:
- Page numbers
- Table of contents
- Cover sheets
- Mixed .pdf and .docx uploads

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Background

This app was inspired by my father, who was occasionally asking me to take stories that he had written using Microsoft Word and render a full-length .pdf file to submit to Staples for publishing as a hard-cover book.  This is an effort to allow him to do it himself without waiting for me to finish.  This turned out to be quite challenging due to the proprietary nature of the .docx file format.

## Install

Install [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) on your system.  

Due to a warning encountered running **LibreOffice** on the command line, you may also need to install the Java components for the software:
```
sudo apt-get install libreoffice-java-common -y
```
If you haven't already done so, install Python3 and PIP:
```
sudo apt install python3 -y
sudo apt install python3-pip -y
```
Install Flask, PyPDF2, FPDF, and pdf.tocgen:
```
sudo pip3 install flask -y
sudo pip3 install pypdf2 -y
sudo pip3 install FPDF -y
sudo pip3 install pdf.tocgen -y
```
Clone the project:
```
git clone https://github.com/rbrutherford3/docx-Publisher.git
```
Optionally adjust the **Flask** settings prior to running:
```
export FLASK_DEBUG=0
export FLASK_ENV=development
```
Run the program:
```
cd /path/to/docxpublisher
python3 flask -m flask run
```
You should see something like the following:
```
 * Environment: development
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```
This means you can now go to `localhost:5000` or `127.0.0.1:5000` in your browser to use the program.

You can also use [**Gunicorn**](https://gunicorn.org/) to set up this project for production, but that is outside the scope of this document

## Usage

1. Simply navigate to the indicated URL
1. Click the **Browse...** button
1. Select multiple .docx files to upload
1. Click **Upload** and wait for the system to convert the files to .pdf
1. Arrange the order of the files by clicking the **Up** and **Down** buttons and optionally rename them
1. Select any options such as adding page numbers or table of contents and specify their criteria
1. Click **Merge** and, if applicable, select a location to download the merged .pdf file

## Contributing

Please contact rbrutherford3 on GitHub if interested in contributing.

## License

[MIT © Robert Rutherford](../LICENSE)

## Acknowledgements

Thanks to Dad for providing the inspiration for this program, and for putting up with me over the years.
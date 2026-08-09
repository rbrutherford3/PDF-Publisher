# PDF Publisher

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

This is a Flask app that takes uploaded .doc, .docx, .odt, and .pdf files, converts them to .pdf, allows the user to arrange and rename them, optionally include page numbers and a table of contents (including embedded PDF bookmarks) and then merges them into one big file.

Go to [https://spiffindustries.com/pdfpublisher/](https://spiffindustries.com/pdfpublisher/) to try it!

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

1. Install [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) and the Java components required by the conversion step:
```
sudo apt-get update
sudo apt-get install -y libreoffice libreoffice-java-common
```

2. Install Python 3 and pip if they are not already available:
```
sudo apt-get install -y python3 python3-pip
```

3. Clone the project and change into the repository directory:
```
git clone https://github.com/rbrutherford3/PDF-Publisher.git
cd PDF-Publisher
```

4. Install the Python dependencies from the project requirements file:
```
sudo pip3 install -r requirements.txt
```

5. Set the reCAPTCHA and CloudConvert environment variables required by the app before running it:
```
export RECAPTCHA_SITE_KEY="your-site-key"
export RECAPTCHA_SECRET_KEY="your-secret-key"
export CLOUDCONVERT_LIVE_API_KEY="your-live-cloudconvert-api-key"
export CLOUDCONVERT_SANDBOX_API_KEY="your-sandbox-cloudconvert-api-key"
```
Optional: opt back into the sandbox environment if needed:
```
export CLOUDCONVERT_SANDBOX=true
```
If you are deploying to Vercel, set the same values in your Vercel project environment variables so the app can access them at runtime.

6. Optionally adjust the **Flask** settings prior to running:
```
export FLASK_DEBUG=0
export FLASK_ENV=development
```

7. Run the program:
```
python3 -m flask run
```

You should see something like the following:
```
 * Environment: development
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

This means you can now go to `localhost:5000` or `127.0.0.1:5000` in your browser to use the program.

This project is also compatible with [Vercel](https://vercel.com/), and the same requirements file is used for its Python dependencies.

You can also use [**Gunicorn**](https://gunicorn.org/) to set up this project for production, but that is outside the scope of this document.

## Usage

1. Simply navigate to the indicated URL
1. Click the **Browse...** button
1. Select multiple .doc, .docx, .odt, and .pdf files to upload
1. Click **Upload** and wait for the system to convert the files to .pdf
1. Arrange the order of the files by clicking the **Up** and **Down** buttons and optionally rename them
1. Select any options such as adding page numbers or table of contents and specify their criteria
1. Click **Merge** and, if applicable, select a location to download the merged .pdf file

For manual CloudConvert testing, open `/cloudconvert/test`, provide an API key if one is not already configured in the environment, upload a `.doc`, `.docx`, or `.odt` file, and the app will return the converted PDF.

## Contributing

Please contact rbrutherford3 on GitHub if interested in contributing.

## License

[MIT © Robert Rutherford](../LICENSE)

## Acknowledgements

Thanks to Dad for providing the inspiration for this program, and for putting up with me over the years.

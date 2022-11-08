// Function to swap two list items when clicking the "up" button, including their custom title
function up(a) {
	var listNum = parseInt(a.id);
	var a = document.getElementById(listNum - 1);
	var b = document.getElementById(listNum);
	a.parentNode.insertBefore(b, a);
	a.id = listNum;
	b.id = listNum - 1;
	var c = document.getElementById("title" + (listNum - 1));
	var d = document.getElementById("title" + listNum);
	c.id = "title" + listNum;
	d.id = "title" + (listNum - 1);
	disableButtons()
}

// Function to swap two list items when clicking the "down" button, including their custom title
function down(a) {
	var listNum = parseInt(a.id);
	var a = document.getElementById(listNum + 1);
	var b = document.getElementById(listNum);
	a.parentNode.insertBefore(a, b);
	a.id = listNum;
	b.id = listNum + 1;
	var c = document.getElementById("title" + (listNum + 1));
	var d = document.getElementById("title" + listNum);
	c.id = "title" + listNum;
	d.id = "title" + (listNum + 1);	
	disableButtons()
}

// Enable all buttons except the top "up" button and bottom "down" button
function disableButtons() {
	numButtons = parseInt(document.getElementById("pdfslen").value);
	for (i = 0; i < numButtons; i++) {
		var buttonUp = document.getElementById("up" + i)
		if (parseInt(buttonUp.parentNode.id) == 0)
			buttonUp.style.visibility = "hidden";
		else
			buttonUp.style.visibility = "visible";		
		var buttonDown = document.getElementById("down" + i)
		if (parseInt(buttonDown.parentNode.id) == (numButtons - 1))
			buttonDown.style.visibility = "hidden";
		else
			buttonDown.style.visibility = "visible";
	}
}

// Enable controls for page numbers only if enabling page numbers, and vice-versa
function pageNumberControls() {
	document.getElementById("pagenumberformat").disabled = !document.getElementById("pagenumbers").checked;
	document.getElementById("pagenumberfont").disabled = !document.getElementById("pagenumbers").checked;
	document.getElementById("pagenumbersize").disabled = !document.getElementById("pagenumbers").checked;
	document.getElementById("pagenumbermargin").disabled = !document.getElementById("pagenumbers").checked;
}

// Compile list of pdfs and their titles in the specified order upon submission
function submitPDF() {
	var pdflist = document.getElementById("pdforder");
	var formatted = "";
	var titles = ""
	for (i = 0; i <= pdflist.lastElementChild.id; i++) {
		formatted = formatted + document.getElementById(i).getAttribute("data-filename");
		titles = titles + document.getElementById("title" + i).value;
		if (i < pdflist.lastElementChild.id) {
			formatted = formatted + "$";
			titles = titles + "$";
		}
	}
	document.getElementById("finalorder").value = formatted;
	document.getElementById("titles").value = titles;
}
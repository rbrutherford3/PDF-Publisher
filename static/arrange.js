// Function to swap two list items when clicking the "up" button, including their custom title
function up(a) {
	var listNum = parseInt(a.id);
	var a = document.getElementById(listNum - 1);
	var b = document.getElementById(listNum);
	a.parentNode.insertBefore(b, a);
	reOrder();
}

// Function to swap two list items when clicking the "down" button, including their custom title
function down(a) {
	var listNum = parseInt(a.id);
	var a = document.getElementById(listNum + 1);
	var b = document.getElementById(listNum);
	a.parentNode.insertBefore(a, b);
	reOrder();
}

// Enable controls for page numbers only if enabling page numbers, and vice-versa
function pageNumberControls() {
	document.getElementById("pagenumberformat").disabled = !document.getElementById("pagenumbers").checked;
	document.getElementById("pagenumberfont").disabled = !document.getElementById("pagenumbers").checked;
	document.getElementById("pagenumbersize").disabled = !document.getElementById("pagenumbers").checked;
	document.getElementById("pagenumbermargin").disabled = !document.getElementById("pagenumbers").checked;
}

// Enable controls for table of contents only if enabling table of contents, and vice-versa
function tocControls() {
	document.getElementById("tocheaderfont").disabled = !document.getElementById("toc").checked;
	document.getElementById("tocheadersize").disabled = !document.getElementById("toc").checked;
	document.getElementById("tocheaderspacing").disabled = !document.getElementById("toc").checked;
	document.getElementById("toclistitemfont").disabled = !document.getElementById("toc").checked;
	document.getElementById("toclistitemsize").disabled = !document.getElementById("toc").checked;
	document.getElementById("toclistitemspacing").disabled = !document.getElementById("toc").checked;
	document.getElementById("tocverticalmargin").disabled = !document.getElementById("toc").checked;
	document.getElementById("tochorizontalmargin").disabled = !document.getElementById("toc").checked;
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

// Taken from https://stackoverflow.com/a/59536432/3130769

window.onload = function() {

	let dragged;
	let id;
	let index;
	let indexDrop;
	let list;

	document.addEventListener("dragstart", ({target}) => {
		dragged = target;
		id = target.id;
		list = target.parentNode.children;
		for (let i = 0; i < list.length; i += 1) {
			if (list[i] === dragged){
				index = i;
			}
		}
	});

	document.addEventListener("dragover", (event) => {
		event.preventDefault();
	});

	document.addEventListener("drop", ({target}) => {
		var valid = false;
		if (target.className == "dropzone" && target.id !== id) {
			var newtarget = target
			valid = true;
		}
		else if (target.parentNode.className == "dropzone" && target.parentNode.id !== id) {
			var newtarget = target.parentNode
			valid = true;
		}
		if (valid) {
			dragged.remove( dragged );
			for(let i = 0; i < list.length; i += 1) {
				if(list[i] === newtarget){
					indexDrop = i;
				}
			}
			console.log(index, indexDrop);
			if(index > indexDrop) {
				newtarget.before( dragged );
			} else {
				newtarget.after( dragged );
			}
			reOrder();	
		}
	});
}

// Function to correct the ids of each element after re-ordering
// and adjust visibility of arrows
function reOrder() {
	var ol = document.getElementById("pdforder");
	var node = ol.firstChild;
	var count = 0;
	while (node) {
		if (node.tagName === 'LI') {
			node.id = count;
			node.style.visibility = "visible";
			var t = node.childNodes;
			for(i=0; i < t.length; i++) {
				if (t[i].tagName === 'INPUT' || t[i].tagName === 'LABEL') {
					if (t[i].id.startsWith("up")) {
						t[i].id = "up" + count.toString();
						t[i].style.visibility = "visible";
					}
					else if (t[i].id.startsWith("down")) {
						t[i].id = "down" + count.toString();
						t[i].style.visibility = "visible";
					}
					else if (t[i].id.startsWith("title"))
						t[i].id = "title" + count.toString();
					else if (t[i].id.startsWith("numberingstartlabel")) {
						t[i].id = "numberingstartlabel" + count.toString();
						t[i].setAttribute("for", "numberingstart" + count.toString());
					}
					else if (t[i].id.startsWith("numberingstart"))
						t[i].id = "numberingstart" + count.toString();
				}
			}
			count++;
		}
		node = node.nextSibling;
	}
	var maxCount = count - 1;
	document.getElementById("up0").style.visibility = "hidden";
	document.getElementById("down" + maxCount.toString()).style.visibility = "hidden";

	// Re-loop through elements and show/hide the page number start radio buttons
	var node = ol.firstChild;
	var justdone = false;
	var donecountdown = 2;
	var done = false;
	while (node) {
		if (node.tagName === 'LI') {
			var t = node.childNodes;
			for(i=0; i < t.length; i++) {
				if (t[i].tagName === 'INPUT' || t[i].tagName === 'LABEL') {
					if (t[i].id.startsWith("numberingstart")) {
						if (done || !document.getElementById("pagenumbers").checked)
							t[i].style.visibility = "hidden";
						else
							t[i].style.visibility = "visible";
					}
					else if (t[i].className == "toc")
						justdone = true;
				}
			}
			if (donecountdown == 1 || justdone)
				donecountdown--;
			if (donecountdown == 0)
				done = true;
		}
		node = node.nextSibling;
	}
}

// Function to show or hide the "Table of Contents" item
function toggleTOC() {
	if (document.getElementById("toc").checked)
		document.getElementById("pdforder").firstChild.before(document.getElementById("toclistitem"))
	else {
		var ol = document.getElementById("pdforder");
		var node = ol.firstChild;
		var count = 0;
		while (node) {
			if (node.tagName === 'LI') {
				if (node.getAttribute("data-filename") == "### TABLE OF CONTENTS ###") {
					node.id = "toclistitem";
					node.style.visibility = "hidden";
					var t = node.childNodes;
					for(i=0; i < t.length; i++) {
						if (t[i].tagName === 'INPUT' || t[i].tagName === 'LABEL') {
							if (t[i].id.startsWith("up"))
								t[i].style.visibility = "hidden";
							else if (t[i].id.startsWith("down"))
								t[i].style.visibility = "hidden";
							else if (t[i].id.startsWith("numberingstartlabel"))
								t[i].style.visibility = "hidden";
							else if (t[i].id.startsWith("numberingstart"))
								t[i].style.visibility = "hidden";
						}
					}
					document.getElementById("toclist").append(node);
				}
			}
			node = node.nextSibling;
		}
	}
	reOrder();
}

// Function to show or hide the 
function togglePageNumbers() {
	if (document.getElementById("pagenumbers").checked) {
		document.getElementById("toc").disabled = false;
	}
	else {
		if (document.getElementById("toc").checked) {
			document.getElementById("toc").checked = false;
			tocControls();
			toggleTOC();
		}
		document.getElementById("toc").disabled = true;
	}
	reOrder();
}

// Make sure that an item is selected for page number start if necessary
function checkPageNumberStart() {
	var selection = false;
	if (document.getElementById("pagenumbers").checked) {
		var els = document.getElementsByName("numberingstart");
		for (var i=0; i<els.length; i++) {
			if (els[i].checked) {
				var selected = els[i];
				selection = true;
			}
		}
		if (selection) {
			if (selected.style.visibility == "hidden")
				selection = false;
		}
	}
	else
		selection = true;
	if (selection == false)
		alert("Please select somewhere for page numbering to begin");
	return selection;
}

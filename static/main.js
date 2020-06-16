function send_request(){
	var query = document.getElementById("input-query").value;
	var query_obj = {"query": query};
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function() { 
		if (this.readyState == 4 && this.status == 200) {
			var response = JSON.parse(this.responseText);
			if (response['corrected']['prob'] >= response['diacritic_added']['prob']){
				var result = response['corrected']['result'];
			}
			else{
				var result = response['diacritic_added']['result'];
			}
			
			document.getElementById("corrected-result").innerHTML = "<h3>" + result + "</h3>";
			document.getElementById("suggestion").style.display = "block";
			
			console.log(response['corrected']['result']);
			console.log(response['corrected']['prob']);
		}
	};
	xhttp.open("POST", "/correct", true);
	xhttp.setRequestHeader("content-type", "application/json");
	xhttp.send(JSON.stringify(query_obj));
}

window.addEventListener("keypress", function(e) {
	if (e.keyCode == 13){
	  send_request();
	}
})
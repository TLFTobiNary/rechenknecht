function refreshResults() {
	const newItem = document.getElementById("newitem");
	newItem.hidden=true;
	const resultList = document.getElementById("resultList");
	const haystack = document.getElementById("item").childNodes;
	const search = document.getElementById("itemsearch");
		while (resultList.firstChild) {
			resultList.removeChild(resultList.firstChild);
		}
		resultList.appendChild(newItem);
	if (search.value.length == 0)
		{
			return;
		}
	var hitCount = 0;

	for (const child of haystack) {
		if (child.nodeType == Node.ELEMENT_NODE) {
			const text = child.text;
			const value = child.value;
			if (text.toLowerCase().includes(search.value.toLowerCase())) {
				hitCount++;
				button = document.createElement("button");
				button.append(text);
				button.addEventListener('click', function() {
					selectItem(""+value+"");
				});
				console.log("have value "+value);
				resultList.appendChild(button);
			}
		}

	}
	if (hitCount == 0) {
		document.getElementById("newitem").hidden = false;
	}
}
function selectItem(itemid) {
	console.log("have value "+itemid);
	document.getElementById("item").value=itemid;
	document.getElementById("itemsearch").value = "";
	refreshResults();

}


